from app.stt.whisper_worker import reprocess_audio
from app.stt.mock_stt import MockSTT
import os


def test_whisper_worker_fallback(tmp_path, monkeypatch):
    # Provide a fake filename to simulate transcript
    audio = tmp_path / "i_was_nervous.wav"
    audio.write_bytes(b"fake audio")
    res = reprocess_audio(str(audio))
    assert "transcript" in res
    assert isinstance(res["word_timestamps"], list)


def test_whisper_worker_with_faster_whisper_mock(monkeypatch, tmp_path):
    # Mock faster_whisper present
    class Segment:
        def __init__(self, start, end, text):
            self.start = start
            self.end = end
            self.text = text
    class FakeModel:
        def __init__(self, model_name, device=None):
            pass
        def transcribe(self, path, beam_size=1):
            segs = [Segment(0.0, 1.2, "hello world"), Segment(1.2, 2.0, "I was nervous")]
            return segs, {}
    monkeypatch.setitem(__import__('sys').modules, 'faster_whisper', FakeModel)
    # Monkeypatch import to use our fake class when imported
    monkeypatch.setattr('app.stt.whisper_worker.WhisperModel', FakeModel, raising=False)
    audio = tmp_path / "example.wav"
    audio.write_bytes(b"x")
    res = reprocess_audio(str(audio))
    assert "hello world" in res["transcript"] or "I was nervous" in res["transcript"]
