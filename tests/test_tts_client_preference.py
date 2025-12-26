from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_tts_generate_returns_client_instructions_when_pref_set():
    # Start a session with client_tts preference
    payload = {"session_id":"client1","user_id":"u1","interview_type":"behavioral","persona":"friendly","emotion_opt_in":False,"client_tts": True}
    r = client.post("/v1/sessions/start", json=payload)
    assert r.status_code == 200

    # Request TTS generation — should return use_client_tts with instructions
    tts_payload = {"session_id":"client1","text":"Hello there","persona":"friendly","audio_format":"wav"}
    r2 = client.post("/v1/tts/generate", json=tts_payload)
    assert r2.status_code == 200
    data = r2.json()
    assert data.get("use_client_tts") is True
    assert "tts_instructions" in data
    assert data["tts_instructions"]["text"] == "Hello there"
