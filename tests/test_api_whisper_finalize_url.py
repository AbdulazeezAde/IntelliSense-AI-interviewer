from fastapi.testclient import TestClient
from app.main import app
import os
from unittest.mock import Mock
import app.stt.whisper_worker as ww

client = TestClient(app)


def test_finalize_with_audio_url(monkeypatch, tmp_path):
    # Fake audio content served by a mocked requests.get
    content = b"FAKEAUDIO"

    class FakeResp:
        def __init__(self, content):
            self._content = content
            self.status_code = 200
        def raise_for_status(self):
            return None
        def iter_content(self, chunk_size=8192):
            for i in range(0, len(self._content), chunk_size):
                yield self._content[i:i+chunk_size]

    monkeypatch.setattr('requests.get', lambda url, stream=True, timeout=10: FakeResp(content))

    # Call finalize with an audio URL; the server should download, run reprocessing (fallback), and return a whisper_result
    r = client.post('/v1/sessions/finalize', json={"session_id":"s_url","audio_url":"http://example.com/audio.wav"})
    assert r.status_code == 200
    data = r.json()
    assert data.get('whisper_reprocessed') is True
    assert 'whisper_result' in data and 'transcript' in data['whisper_result']
