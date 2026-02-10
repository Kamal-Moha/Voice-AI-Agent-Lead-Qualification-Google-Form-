from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.plugins import (
    silero,
    aws,
    cartesia,
    google,
    noise_cancellation,
)

# import packages
from google.cloud import storage
import os
from datetime import datetime, timedelta
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

def get_cs_file_url(bucket_name, gcs_path, expire_in=None):
    # Fix the timing bug: calculate "tomorrow" at call time, not boot time
    if expire_in is None:
        expire_in = datetime.utcnow() + timedelta(days=1)
    
    full_path = gcs_path.lstrip('/')

    try:
        # Attempt to generate a signed URL
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(full_path)
        
        # This is where the AttributeError would happen if signing fails
        url = blob.generate_signed_url(expiration=expire_in)
        return url

    except Exception as e:
        # Fallback to public URL if signing fails or credentials lack permissions
        print(f"Signing failed, defaulting to public URL. Error: {e}")
        return f"https://storage.googleapis.com/{bucket_name}/{full_path}"

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
    # Folder-friendly date (YYYY-MM-DD)
    folder_date = datetime.now().strftime("%Y-%m-%d") 
    
    # Precise timestamp for the filename (to avoid overwriting)
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Path inside GCS: i.e "2026-02-10/transcript_room-name_130202.json"
    gcs_path = f"{folder_date}/transcript_{ctx.room.name}_{timestamp}.json"
    
    # Local path for writing the file temporarily on the VM disk
    # We use a simple name locally to avoid needing to create local folders
    filename = f"tmp_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(session.history.to_dict(), f, indent=2)

    # Saving to Google Cloud
    upload_cs_file("voice-ai-call-transcripts", filename, gcs_path)

    public_url = get_cs_file_url("voice-ai-call-transcripts", gcs_path)
    print(f"Transcript for {ctx.room.name} saved to {public_url}")
    
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


#   # Amazon Nova Sonic
#   session = AgentSession(
#     llm=aws.realtime.RealtimeModel(
#         voice="tiffany"
#     ),
#   )

  # STT-LLM-TTS Pipeline
  session = AgentSession(
    stt = cartesia.STT(
        model="ink-whisper"
    ),
    llm=google.LLM(
        model="gemini-3-flash-preview",
    ),
    tts=cartesia.TTS(
        model="sonic-3",
        # voice="f786b574-daa5-4673-aa0c-cbe3e8534c02",
        voice="228fca29-3a0a-435c-8728-5cb483251068"
    ),
    turn_detection=EnglishModel(),
    vad=silero.VAD.load()
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
