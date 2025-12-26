from typing import Dict, Any, List
import os
from pathlib import Path

class BaseSTTProvider:
    async def process_chunk(self, chunk_bytes: bytes):
        raise NotImplementedError

    async def finalize(self) -> Dict[str, Any]:
        raise NotImplementedError


class MockSTTProvider(BaseSTTProvider):
    """Backward compatible mock provider wrapper."""
    def __init__(self, session_id: str):
        from .mock_stt import MockSTT
        self._impl = MockSTT(session_id=session_id)

    async def process_chunk(self, chunk_bytes: bytes):
        # chunk_bytes for mock is actually a UTF-8 string for tests
        await self._impl.process_chunk(chunk_bytes.decode('utf-8'))

    async def finalize(self) -> Dict[str, Any]:
        return await self._impl.finalize()


class VoskSTTProvider(BaseSTTProvider):
    """A simple VOSK-based provider (optional). If VOSK isn't installed or model missing, raise ImportError.

    This provider will attempt real-time partials and produce word-level timestamps.
    """
    def __init__(self, session_id: str, model_path: str = None):
        try:
            from vosk import Model, KaldiRecognizer
        except Exception as e:
            raise ImportError("VOSK not installed or not available") from e
        self.session_id = session_id
        # Determine model path: explicit > env VOSK_MODEL_PATH > ./models/vosk-model-small-*
        if not model_path:
            model_path = os.getenv("VOSK_MODEL_PATH")
            if not model_path:
                # try to auto-detect
                base = Path("models")
                if base.exists():
                    for child in base.iterdir():
                        if child.is_dir() and child.name.startswith("vosk-model"):
                            model_path = str(child)
                            break
        if not model_path:
            raise ValueError("No VOSK model found. Set VOSK_MODEL_PATH or download a model into ./models")
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self._chunks = []

    async def process_chunk(self, chunk_bytes: bytes):
        # push raw audio bytes to recognizer
        self._chunks.append(chunk_bytes)
        self.rec.AcceptWaveform(chunk_bytes)

    async def finalize(self) -> Dict[str, Any]:
        # produce final result
        import json
        final = self.rec.FinalResult()
        # Vosk returns JSON; convert to our schema as best effort
        try:
            parsed = json.loads(final)
            words = parsed.get('result', [])
            transcript = ' '.join(w['word'] for w in words)
            word_timestamps = [{'word': w['word'], 'start_ms': int(w['start']*1000), 'end_ms': int(w['end']*1000), 'confidence': w.get('conf', 1.0)} for w in words]
            # simple filler detection
            filler_words = [ {'word': w['word'], 'start_ms': int(w['start']*1000), 'end_ms': int(w['end']*1000)} for w in words if w['word'].lower() in ('um','uh','like','youknow','you','know') ]
            return {
                'transcript': transcript,
                'word_timestamps': word_timestamps,
                'filler_words': filler_words,
                'pause_segments': [],
                'speech_rate_wpm': int(len(transcript.split())/ (max(1, (word_timestamps[-1]['end_ms'] - word_timestamps[0]['start_ms'])/60000))) if word_timestamps else 0
            }
        except Exception:
            # fallback minimal
            return {'transcript': parsed.get('text','') if isinstance(parsed, dict) else '', 'word_timestamps': [], 'filler_words': [], 'pause_segments': [], 'speech_rate_wpm': 0}
