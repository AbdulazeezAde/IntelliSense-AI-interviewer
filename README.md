# InterviewSense AI — Backend

Minimal FastAPI backend skeleton for InterviewSense AI MVP.

Run locally (development):

- Create a virtual environment, install dependencies from `requirements.txt`.
- Start server: `uvicorn app.main:app --reload --port 8000`

This repo contains modular stubs for STT, LLM, Emotion Detector, TTS, and Scoring Engine to support iterative development and testing.

Client-side TTS (Browser SpeechSynthesis)

- You can use the browser SpeechSynthesis API to avoid server-side TTS costs. To enable client-side TTS for a session, set `client_tts` to true when starting a session:

```bash
curl -X POST http://localhost:8000/v1/sessions/start -H "Content-Type: application/json" -d '{"session_id":"s1","user_id":"u1","interview_type":"behavioral","persona":"friendly","client_tts":true}'
```

- Then call the TTS generate endpoint; the response will include `use_client_tts: true` and `tts_instructions` that the client can use with `speechSynthesis`:

```bash
curl -X POST http://localhost:8000/v1/tts/generate -H "Content-Type: application/json" -d '{"session_id":"s1","text":"Welcome to the mock interview","persona":"friendly"}'
```

- See `app/client/tts_example.html` for an example client implementation that uses these instructions.

Storage providers & CI

- The adapter uses connection string + container for Azure Blob Storage. It creates the container if missing (best for dev). In production, prefer pre-created containers and stricter ACLs.
- The adapter can optionally generate short-lived SAS URLs for secure delivery. Set `AZURE_BLOB_SAS_TTL_SECONDS` (seconds) to a positive integer to enable SAS URL generation for uploaded blobs (example: 3600 for one hour).
- The azure SDK (`azure-storage-blob`) is a runtime dependency only when you enable Azure; the module lazily imports it to avoid hard failures in other environments.
- CI: The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that starts an Azurite service and runs the test suite using a local Azurite emulator. The workflow sets `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_STORAGE_CONTAINER` for the emulator.

STT: VOSK & Whisper

- See `docs/stt_whisper.md` for instructions on installing VOSK models and enabling Whisper reprocessing for higher-accuracy post-processing.
- Whisper reprocessing can be triggered by calling `POST /v1/sessions/finalize` with the `audio_path` field pointing to a server-accessible audio file. The response will include `whisper_result` when reprocessing succeeds.

Azure storage notes

- We support storing TTS artifacts in a remote object store. For Azure set `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_STORAGE_CONTAINER`.
- Example env variables (add to `.env` for local dev):

```
# Azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=...;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
AZURE_STORAGE_CONTAINER=interviews
AZURE_BLOB_SAS_TTL_SECONDS=3600

# Redis cache (optional)
REDIS_URL=redis://localhost:6379
```

CI note: The repository CI includes a focused test step that runs `tests/test_audio_fetcher.py::test_fetch_with_retries` to ensure the session-based HTTP fetch (with retries) remains covered and prevents accidental regressions.
