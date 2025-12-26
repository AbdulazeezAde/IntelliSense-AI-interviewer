from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_update_client_tts_preference():
    session_id = "pref1"
    payload = {"session_id":session_id,"user_id":"u1","interview_type":"behavioral","persona":"neutral","emotion_opt_in":False,"client_tts": False}
    r = client.post("/v1/sessions/start", json=payload)
    assert r.status_code == 200

    # Toggle client_tts on
    r2 = client.patch(f"/v1/sessions/{session_id}/preferences", json={"client_tts": True})
    assert r2.status_code == 200
    assert r2.json()["updated"]["client_tts"] is True

    # Now TTS generate should return client instructions
    tts_payload = {"session_id":session_id,"text":"Hello","persona":"neutral"}
    r3 = client.post("/v1/tts/generate", json=tts_payload)
    assert r3.status_code == 200
    data = r3.json()
    assert data.get("use_client_tts") is True


def test_toggle_emotion_opt_in_affects_ws():
    session_id = "pref2"
    payload = {"session_id":session_id,"user_id":"u2","interview_type":"behavioral","persona":"neutral","emotion_opt_in": False}
    r = client.post("/v1/sessions/start", json=payload)
    assert r.status_code == 200

    # Simulate transcript - should have no emotion events initially
    with client.websocket_connect(f"/v1/ws/audio/{session_id}") as ws:
        ws.send_json({"type":"sim_transcript","transcript":"I was nervous about this"})
        data = ws.receive_json()
        assert data["type"] == "turn_result"
        assert data["result"]["emotion_events"] == []

    # Toggle emotion opt in
    r2 = client.patch(f"/v1/sessions/{session_id}/preferences", json={"emotion_opt_in": True})
    assert r2.status_code == 200

    # Now simulate again: should produce emotion events
    with client.websocket_connect(f"/v1/ws/audio/{session_id}") as ws2:
        ws2.send_json({"type":"sim_transcript","transcript":"I was nervous about this"})
        data2 = ws2.receive_json()
        assert data2["type"] == "turn_result"
        assert len(data2["result"]["emotion_events"]) >= 1
