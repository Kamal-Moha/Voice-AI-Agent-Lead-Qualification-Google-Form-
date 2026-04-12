# Voice AI Agent for a Plumbing Company
This Voice AI Agent helps plumbers to immediately call their leads after they fill a Google Form. The voice agent calls the lead, qualifies it by asking qualifying questions, records the call and is able to book the job. It then creates a summary from the call and saves it into Google Sheets.

## Demo: This Voice AI Agent in Action



## Table of contents
- [Problem Statement](#problem-statement)
- [Traditional Approach used by businesses](#traditional-approach-followed-by-most-businesses)
- [Solution](#solution)
- [Architecture](#architecture)
- [How this Voice AI System works](#how-this-voice-ai-system-works)
- [Benefits](#benefits)
- [Tech stack used](#tech-stack-used)
- [Resources](#resources)

## Problem Statement

Home service businesses are bombarded by service inquiries specially during peak operation seasons/time and most of these businesses don't have a system to handle this surge. 

This leads to them losing money because these interested leads are not reached out to and these causes them to lose money.

## Traditional approach followed by most businesses

In my findings I have noticed that business owners follow this traditional approach;
1. Business owner (Marketer) runs Facebook Lead Ads.
2. User (Lead) clicks.
3. They fill your form.

Then what?

Most businesses just… sit there. Waiting. Hoping someone from your team will call manually.

Meanwhile, your hot high-intent lead turns cold. They have reached to three other competitors. And you still haven’t called them.

That’s not lead generation. That’s money bleeding.

## Solution

I have created a Voice AI system that's able to;
- Call your leads in less than 60 seconds as soon as they fill an inquiry form (i.e Google Form). 
- Qualify your leads.
- Book appointments on your calendars
- Update your CRM

The Voice AI Agent qualifies the lead in real-time, books appointments on your calendar, and sends you the legit leads. It then analyzes the call, categorizes the lead and instantly updates your CRM.

## Architecture
<img width="889" height="462" alt="architecture" src="https://github.com/user-attachments/assets/1241c494-e331-49b8-b752-3db1a04b270d" />


## How this Voice AI System works

The Voice AI Agent takes these actions as soon as an inquiry form is filled;
1. Call the lead in less than 60 seconds
2. Have a natural conversation with this user (lead).
3. Understand the needs of this user and qualify them
4. Book a job/appointment on the business calendar
5. Categorize the lead (whether lead is high/medium/low)
6. Save call summary on a CRM (i.e Google Sheets)
<img width="2160" height="800" alt="Form + Voice AI" src="https://github.com/user-attachments/assets/3cbcdcd7-0ee5-4be8-8f04-e8a39fa32068" />


## Benefits
With this Voice AI Agent implemented, home service businesses;
1. Will never lose a hot lead again.
2. No more leads will go to your competition.
3. Will reduce your Customer Per Acquisition (CAC) cost.
4. Will increase your revenue
5. Will get a lead generation system that books jobs/appointments 24/7/365 and is guaranteed to get better.

## Tech stack used
1. **Livekit**: To build the Voice AI Agent
2. **Inngest (FastAPI)**: As the Agent Orchestrator
3. **Twilio**: Phone carrier
4. **PydanticAI**: To summarize the call transcription & provide structured output.
5. **Google Apps Script**: To trigger a webhook when user fills a Google Form. It also uploads call summary to Google Sheets
6. **Cloud Platforms**: Deployed on Google Cloud (GCP).
7. **Github Actions**: To automate deployments by having a CI/CD pipeline.

## Resources
Watch the full video of this Voice AI Agent in use.
https://www.youtube.com/watch?v=waItX1pYJvQ&pp=0gcJCdkKAYcqIYzv
