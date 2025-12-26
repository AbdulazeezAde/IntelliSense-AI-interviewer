from fastapi.testclient import TestClient
from app.main import app
import base64

client = TestClient(app)


def test_tts_generate_and_cache():
    payload = {"session_id":"s1","text":"Hello interviewer","persona":"friendly","emotion":"encouraging","audio_format":"wav"}
    r = client.post("/v1/tts/generate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "audio_url" in data and "duration_ms" in data

    # Repeating should hit cache and return same audio_url
    r2 = client.post("/v1/tts/generate", json=payload)
    assert r2.status_code == 200
    assert r2.json()["audio_url"] == data["audio_url"]


def test_tts_ws_streaming():
    with client.websocket_connect("/v1/tts/ws/s1") as ws:
        ws.send_json({"type":"generate","text":"Welcome to the interview","persona":"neutral","emotion": None})
        got_chunk = False
        while True:
            msg = ws.receive_json()
            if msg["type"] == "audio_chunk":
                # Decode to ensure valid base64
                b = base64.b64decode(msg["data"].encode("ascii"))
                assert b.startswith(b"AUDIO")
                got_chunk = True
            elif msg["type"] == "complete":
                assert "audio_url" in msg
                assert got_chunk
                break
            else:
                assert False, f"Unexpected msg: {msg}"
