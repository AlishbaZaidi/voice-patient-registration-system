# Voice AI Patient Registration System

## Overview
A voice-based patient registration system: a caller dials in, converses naturally with an AI agent to register as a new patient, and the collected data is persisted to a database and exposed via a REST API.

## What's Working (Verified)

### Backend REST API — fully functional and deployed
- Built with FastAPI, SQLAlchemy, and Pydantic
- Deployed live on Railway with PostgreSQL for real persistence across server restarts
- All 5 required endpoints implemented and tested:
  - `GET /patients` (with `last_name`, `date_of_birth`, `phone_number` filters)
  - `GET /patients/:id`
  - `POST /patients`
  - `PUT /patients/:id` (partial updates supported)
  - `DELETE /patients/:id` (soft-delete via `deleted_at` timestamp, not a hard delete)
- Server-side validation on every field per the spec (name format, phone format, valid US state, ZIP format, no future birthdates)
- Consistent `{ "data": {...}, "error": null }` response envelope
- Proper HTTP status codes (200, 201, 404, 422, 500)
- Logging of registration events to stdout
- Verified independently via curl (see Verification section below) — confirmed data persists correctly

### Voice conversation agent — verified via live test calls
- Built with Vapi, using Groq (Custom LLM integration) for the LLM
- Conducts a natural, multi-turn conversation rather than a rigid IVR menu
- Collects all required fields conversationally, one or two at a time
- Validates input and re-prompts on invalid data (e.g., asks again when a phone number doesn't have 10 digits)
- Offers optional fields (insurance, emergency contact, preferred language) rather than always asking
- Reads back all collected information and asks for explicit confirmation before saving
- Handles live corrections mid-call (e.g., a caller correcting a misheard detail)
- **Duplicate detection (bonus)**: calls a `find_patient_by_phone` check before registration; when an existing record is found, offers to update instead of create — confirmed working in test calls

## Known Limitation: Voice Agent → Backend Connectivity

The voice agent's tool calls (`create_patient` / `update_patient`) do not reliably reach the deployed backend during live voice calls, despite the backend itself being fully functional and independently verified.

**Debugging trail:**
1. Initial setup used `llama-3.3-70b-versatile` on Groq. This model was decommissioned by Groq on August 16, 2026, and every call failed immediately with a generic `400` error.
2. Switched to `openai/gpt-oss-120b`. Discovered (via direct API testing) that this and every other tool-capable model currently available on Groq are "reasoning" models that stream non-standard `reasoning`/`channel` fields alongside `content` — likely incompatible with how Vapi's response parser expects a standard OpenAI-format stream.
3. Verified the Groq API key and model work correctly in isolation via direct curl requests to `api.groq.com`.
4. With a working LLM connection, voice conversations began completing successfully end-to-end (natural dialogue, corrections, confirmations, duplicate detection all functioning).
5. Verified the backend independently via direct curl `POST /patients` — confirmed `201 Created` and persisted data.
6. Added CORS middleware to the FastAPI app as a further troubleshooting step, in case preflight requests were being silently rejected.
7. Despite all of the above, server logs show zero incoming requests from Vapi during live voice calls at the moment the agent reports calling `create_patient` — the tool call is not reaching the backend, and the root cause (something in how Vapi's Custom LLM tool-calling serializes/sends the request) was not resolved within the time available.

**Next steps if given more time:** insert a request-logging proxy (e.g., webhook.site) between Vapi and the Railway API to capture Vapi's exact outbound tool-call payload, which would show definitively whether the request is malformed, mis-routed, or never sent.

## Verification (Backend, Independent of Vapi)

```bash
curl -X POST https://voice-patient-registration-system-production.up.railway.app/patients \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"Patient","date_of_birth":"1990-01-01","sex":"Male","phone_number":"5559998888","address_line_1":"1 Test St","city":"Testville","state":"IL","zip_code":"60601"}'
```
Returns `201 Created` with the persisted record. Confirmed retrievable afterward via `GET /patients?last_name=Patient`.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic, PostgreSQL
- **Hosting**: Railway
- **Voice/Telephony**: Vapi
- **LLM**: Groq (Custom LLM integration via OpenAI-compatible endpoint)

## Environment Variables
- `DATABASE_URL` — Postgres connection string (auto-provided by Railway; falls back to local SQLite if unset, for local development)

## Setup (Local Development)
```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for interactive API testing.

## Links
- **Repository**: https://github.com/AlishbaZaidi/voice-patient-registration-system
- **Live API**: https://voice-patient-registration-system-production.up.railway.app
- **API Docs (Swagger)**: https://voice-patient-registration-system-production.up.railway.app/docs