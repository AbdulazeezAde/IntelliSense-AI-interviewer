from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_client_demo_served():
    r = client.get("/client/siri_demo.html")
    assert r.status_code == 200
    assert "Siri-like demo" in r.text or "InterviewSense — Siri-like demo" in r.text