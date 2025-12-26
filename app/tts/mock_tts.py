async def generate_tts(session_id: str, text: str, persona: str, emotion: str | None = None, audio_format: str = "wav", pitch: float | None = None, rate: float | None = None):
    # Stub: in production, generate real audio and return a hosted URL or streaming endpoint (Azure blob is supported in this repo)
    return {"audio_url": f"https://mock-tts.local/{session_id}/tts.wav","duration_ms": len(text.split())*80}
