import asyncio
import base64
from typing import Dict, Any

class BaseTTSProvider:
    async def generate(self, session_id: str, text: str, persona: str, emotion: str | None = None, audio_format: str = "wav", pitch: float | None = None, rate: float | None = None) -> Dict[str, Any]:
        raise NotImplementedError

class MockTTSProvider(BaseTTSProvider):
    """Very small mock provider that returns an audio URL and synthetic bytes for streaming.
    This simulates generation latency and streaming and persists artifacts to filesystem storage when available.
    """
    async def generate(self, session_id: str, text: str, persona: str, emotion: str | None = None, audio_format: str = "wav", pitch: float | None = None, rate: float | None = None) -> Dict[str, Any]:
        # Simulate generation latency proportional to text length
        await asyncio.sleep(min(0.2 + len(text) * 0.005, 2.0))
        # Produce a fake binary payload (base64) representing audio bytes for streaming tests
        payload = (f"AUDIO:{persona}:{emotion or 'none'}:" + text).encode("utf-8")
        b64 = base64.b64encode(payload).decode("ascii")
        duration_ms = max(300, len(text.split()) * 80)
        # Persist artifact: prefer Azure Blob (if configured), otherwise filesystem, otherwise mock URL
        filename = f"{session_id}_{abs(hash(text))%100000}.{audio_format}"
        audio_url = None
        # Try Azure Blob first
        try:
            from ..storage.azure_blob import upload_base64
            from ..core.config import settings as cfg
            if cfg.AZURE_STORAGE_CONNECTION_STRING and cfg.AZURE_STORAGE_CONTAINER:
                blob_url = upload_base64(cfg.AZURE_STORAGE_CONTAINER, filename, b64)
                if blob_url:
                    audio_url = blob_url
        except Exception:
            audio_url = None

        # Fallback to filesystem
        if not audio_url:
            try:
                from ..storage.filesystem import save_base64
                saved_path = save_base64(filename, b64)
                audio_url = saved_path
            except Exception:
                audio_url = f"https://mock-tts.local/{session_id}/{filename}"

        return {
            "audio_url": audio_url,
            "duration_ms": duration_ms,
            "audio_b64": b64,
            "voice_parameters_used": {"persona": persona, "emotion": emotion, "pitch": pitch, "rate": rate}
        }

# Export a singleton for simplicity
_provider = MockTTSProvider()

def get_provider():
    return _provider
