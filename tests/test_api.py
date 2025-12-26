import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_start_session():
    payload = {"session_id":"s1","user_id":"u1","interview_type":"behavioral","persona":"friendly"}
    r = client.post("/v1/sessions/start", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "question_id" in data and "question_text" in data

def test_finalize_session():
    r = client.post("/v1/sessions/finalize", json={"session_id":"s1"})
    assert r.status_code == 200
    data = r.json()
    assert "overall_score" in data
