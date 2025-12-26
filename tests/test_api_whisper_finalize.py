from fastapi.testclient import TestClient
from app.main import app
import tempfile

client = TestClient(app)

def test_finalize_with_audio_path(tmp_path):
    # Create a fake audio file
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"FAKE")
    r = client.post("/v1/sessions/finalize", json={"session_id":"s_audio","audio_path":str(audio)})
    assert r.status_code == 200
    data = r.json()
    # Expect whisper_result to be present and contain a transcript key
    assert "whisper_reprocessed" in data and data["whisper_reprocessed"] is True
    assert "whisper_result" in data
    assert "transcript" in data["whisper_result"]
