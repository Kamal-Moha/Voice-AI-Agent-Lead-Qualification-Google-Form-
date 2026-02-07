from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import (
    aws,
    noise_cancellation,
)

# import packages
from google.cloud import storage
import os
from datetime import datetime
import json, httpx, logging
import inngest

load_dotenv()

# Create an Inngest client
inngest_client = inngest.Inngest(
    app_id="Lead Qualification - Voice AI Agent",
    logger=logging.getLogger("uvicorn"),
    is_production=True
)

# define function that uploads a file from the bucket
def upload_cs_file(bucket_name, source_file_name, destination_file_name):
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(source_file_name)

    return True

from datetime import datetime, timedelta

# define function that generates the public URL, default expiration is set to 24 hours
def get_cs_file_url(bucket_name, file_name, expire_in=datetime.today() + timedelta(1)):
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    url = bucket.blob(file_name).generate_signed_url(expire_in)

    return url


class ContextAgent(Agent):
  def __init__(self, context_vars=None) -> None:
    instructions = """
        You are a helpful service assistant.

        The user's name is {name} and their phone is {phone}.
        They reported an issue: {issue} at a {place_type}.
        The issue started at: {issue_start}, urgency: {job_urgency}.
        Service address: {address}, service needed: {needed}.

        Preferred visit date: {preferred_visit_date}, time: {preferred_visit_time}.
    """

    if context_vars:
      instructions = instructions.format(**context_vars)

    super().__init__(instructions=instructions)

  async def on_enter(self):
    self.session.generate_reply(
        instructions="Greet ther user and offer your assistance. You should start by speaking in English."
    )

server = AgentServer()

@server.rtc_session(agent_name="test-agent")
async def my_agent(ctx: agents.JobContext):
  # --------------

  await ctx.connect()
  participant = await ctx.wait_for_participant()

  print(participant)
  print(f"Participant Attributes: {participant.attributes}")
  print(f"Participant Name: {participant.attributes['name']}")

  async def write_transcript():
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Curent Date: {current_date}")
    # This example writes to the temporary directory, but you can save to any location
    filename = f"/transcript_{ctx.room.name}_{current_date}.json"
    with open(filename, 'w') as f:
        json.dump(session.history.to_dict(), f, indent=2)

    # Saving to Google Cloud
    upload_cs_file("voice-ai-call-transcripts", filename, filename)

    public_url = get_cs_file_url("voice-ai-call-transcripts", filename)
    print(f"Transcript for {ctx.room.name} saved to {public_url}")

    # print(f"Transcript for {ctx.room.name} saved to {filename}")


    # Prepare data to trigger event in inngest
    payload = {
        "transcript_url": public_url,
        "user": {
          "name": participant.attributes['name'],
          "phone": participant.attributes['sip.phoneNumber']
        }
    }

    # Sending event to inngest
    await inngest_client.send(
        inngest.Event(
            name="livekit/call.completed",
            data=payload
        )
    )

    return f"Call transcript {public_url} sent and inngest event triggered"

  ctx.add_shutdown_callback(write_transcript)


  # Amazon Nova Sonic
  session = AgentSession(
    llm=aws.realtime.RealtimeModel(
        voice="tiffany"
    ),
  )


  await session.start(
     
    room=ctx.room,
    agent=ContextAgent(participant.attributes),
    room_options=room_io.RoomOptions(
        audio_input=room_io.AudioInputOptions(
            noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
        ),
    ),
  )

  await session.generate_reply(
    instructions="Greet the user and offer your assistance. You should start by speaking in English."
  )


if __name__ == "__main__":
    agents.cli.run_app(server)
