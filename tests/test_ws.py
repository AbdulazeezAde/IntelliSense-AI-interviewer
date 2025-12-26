from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ws_sim_transcript():
    with client.websocket_connect("/v1/ws/audio/s1") as websocket:
        payload = {"type":"sim_transcript","transcript":"I was nervous but I fixed the bug and the result improved by 20%."}
        websocket.send_json(payload)
        data = websocket.receive_json()
        assert data["type"] == "turn_result"
        res = data["result"]
        assert "turn_id" in res
        assert "llm" in res
        assert "turn_score" in res["llm"] or "component_scores" in res["llm"]
