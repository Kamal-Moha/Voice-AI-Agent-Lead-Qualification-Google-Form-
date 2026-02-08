import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
import aiohttp
import os
import requests, httpx, json
import asyncio
from typing import Literal

from dotenv import load_dotenv

from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest, SIPParticipantInfo

from pydantic import BaseModel
from pydantic_ai import Agent, DocumentUrl

load_dotenv()

logger = logging.getLogger(__name__)
headers = {'content-type': 'application/json'}

app = FastAPI()

class InputData(BaseModel):
  issue_start: str
  job_urgency: str
  name: str
  phone: str
  place_type: str
  preferred_date_for_visit: str
  preferred_time_for_visit: str
  problem: str
  service_address: str
  service_needed: str

class JsonFileOutput(BaseModel):
    tool_calls: list[str]
    tool_call_results: list[str]
    lead_intent: Literal["High", "Medium", "Low"]
    summary: str

class Transcript(BaseModel):
  url: str

# Configuration
room_name = "my-room"
agent_name = "test-agent"
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

# async def make_call(name: str, phone_number: str, story: str) -> None:
async def make_call(data: InputData) -> None:
  """Create a dispatch and add a SIP participant to call the phone number"""
  lkapi = api.LiveKitAPI()

  # Create agent dispatch
  logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")
  dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata=data.phone
        )
  )
  logger.info(f"Created dispatch: {dispatch}")
  print(f"Created dispatch: {dispatch}")


  dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
  print(f"there are {len(dispatches)} dispatches in {room_name}")

  # Create SIP participant to make the call
  if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
      logger.error("SIP_OUTBOUND_TRUNK_ID is not set or invalid")
      return

  logger.info(f"Dialing {data.phone} to room {room_name}")

  participant_attributes = {
    "name": data.name,
    "phone": data.phone,
    "issue": data.problem,
    "place_type": data.place_type,
    "issue_start": data.issue_start,
    "job_urgency": data.job_urgency,
    "address": data.service_address,
    "needed": data.service_needed,
    "preferred_visit_date": data.preferred_date_for_visit,
    "preferred_visit_time": data.preferred_time_for_visit,
}

  try:
      # Create SIP participant to initiate the call
      sip_participant = await lkapi.sip.create_sip_participant(
          CreateSIPParticipantRequest(
              room_name=room_name,
              sip_trunk_id=outbound_trunk_id,
              sip_call_to=data.phone,
              participant_identity="phone_user",
              participant_name = data.name,
              krisp_enabled = True,
              wait_until_answered = True,
              play_dialtone = True,
              participant_attributes=participant_attributes

          )
      )
      logger.info(f"Created SIP participant: {sip_participant}")
  except Exception as e:
      logger.error(f"Error creating SIP participant: {e}")

  # Close API connection
  await lkapi.aclose()


# FUNCTION 2 - Analyze transcript
async def analyze_transcript(transcript: Transcript):
  agent: Agent[None, str] = Agent(
    'github:openai/gpt-4.1',
    system_prompt="You are a helpful agent tasked to interpret documents",
    output_type=JsonFileOutput,
  )
  print(f"Transcript: {transcript}")
  result = await agent.run(
    [
        'Summarize this document. Tell me what are the main actions taken and what are the tool calls that have been made',
        DocumentUrl(url=transcript),
    ]
  )

  print(f"Result: {result}")
  return result.output.model_dump()


# FUNCTION 3 - Sending info to Google Sheets. This function sends data to your Google Apps Script Web App
async def send_to_google_sheet(data: JsonFileOutput, name: str, phone_number: str):
    # !!! PASTE YOUR WEB APP URL HERE !!!
    apps_script_url = os.getenv("APPS_SCRIPT_WEB_APP")

    try:
      # Adding 'name' and 'phone_number' into the dictionary
      data['name'] = name
      data['phone_number'] = phone_number
      payload = json.dumps(data)
      print(f"PAYLOAD: {payload}")
      
      # Make the POST request
      response = requests.post(apps_script_url, data=payload, headers=headers)
      response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

      return f"✅Successfully sent data to Google Sheet {response.json()}"

    except requests.exceptions.RequestException as e:
      return f"❌ Failed to send data to Google Sheet: {e}"

# Create an Inngest client
inngest_client = inngest.Inngest(
    app_id="Lead Qualification - Voice AI Agent",
    logger=logging.getLogger("uvicorn"),
    is_production=True
)

# Create the inngest function to handle what should happen after user fills the google form
@inngest_client.create_function(
    fn_id="google_form_submitted",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="google/form.submitted"),
)
async def google_form_submitted(ctx: inngest.Context) -> str:
    print(f"Event: {ctx.event}")

    data = InputData(**ctx.event.data)
    # Calling the user
    await ctx.step.run("calling_the_user", make_call, data)


# Creating the Inngest function to handle what should happen when the calls is completed
@inngest_client.create_function(
    fn_id="livekit_call_completed",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="livekit/call.completed"),
)
async def livekit_call_completed(ctx: inngest.Context) -> str:
    print(f"Event: {ctx.event}")

    transcript_url = ctx.event.data["transcript_url"]

    # Step 1 - Transcribe the call
    call_analysis = await ctx.step.run("Transcribing the call", analyze_transcript, transcript_url)

    # Step 2 - Sending info to Google Sheets
    await ctx.step.run("Sending to Google Sheets", send_to_google_sheet, call_analysis, ctx.event.data["user"]['name'], ctx.event.data["user"]['phone'])

# Serve the Inngest endpoint
inngest.fast_api.serve(app, inngest_client, [google_form_submitted, livekit_call_completed])
