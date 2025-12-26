from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_emotion_opt_out_results_in_empty_events():
    # Start session without emotion opt-in
    payload = {"session_id":"s_noem","user_id":"u1","interview_type":"behavioral","persona":"neutral","role_info":{},"emotion_opt_in": False}
    r = client.post("/v1/sessions/start", json=payload)
    assert r.status_code == 200

    with client.websocket_connect("/v1/ws/audio/s_noem") as websocket:
        websocket.send_json({"type":"sim_transcript","transcript":"I was nervous but I fixed the bug."})
        data = websocket.receive_json()
        assert data["type"] == "turn_result"
        res = data["result"]
        assert res["emotion_events"] == []


def test_emotion_opt_in_produces_events():
    payload = {"session_id":"s_em","user_id":"u2","interview_type":"behavioral","persona":"neutral","role_info":{},"emotion_opt_in": True}
    r = client.post("/v1/sessions/start", json=payload)
    assert r.status_code == 200

    with client.websocket_connect("/v1/ws/audio/s_em") as websocket:
        websocket.send_json({"type":"sim_transcript","transcript":"I was nervous and anxious."})
        data = websocket.receive_json()
        assert data["type"] == "turn_result"
        res = data["result"]
        assert len(res["emotion_events"]) >= 1
