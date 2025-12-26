from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

with client.websocket_connect("/v1/ws/audio/s1") as ws:
    ws.send_json({"type":"sim_transcript","transcript":"I was nervous but I fixed the bug and the result improved by 20%."})
    data = ws.receive_json()
    print("GOT:", data)
