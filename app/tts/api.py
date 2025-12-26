from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from .provider import get_provider
from .cache import get_cached, set_cached
import base64

router = APIRouter()

class TTSRequest(BaseModel):
    session_id: str
    text: str
    persona: str = "neutral"
    emotion: Optional[str] = None
    audio_format: str = "wav"
    pitch: Optional[float] = None
    rate: Optional[float] = None

from ..state.session_store import get_session

class TTSResponse(BaseModel):
    audio_url: str | None = None
    duration_ms: int | None = None
    voice_parameters_used: dict | None = None
    use_client_tts: bool | None = False
    tts_instructions: dict | None = None

@router.post("/generate", response_model=TTSResponse)
async def generate_tts(req: TTSRequest):
    # Validate basic constraints
    if not req.text:
        raise HTTPException(status_code=400, detail="text is required")

    # If session prefers client-side TTS, return instructions for browser SpeechSynthesis
    sess = get_session(req.session_id)
    if sess.get("client_tts"):
        # Provide a small set of voice params mapping persona -> rate/pitch
        persona_map = {
            "friendly": {"rate": 1.05, "pitch": 1.1},
            "neutral": {"rate": 1.0, "pitch": 1.0},
            "strict": {"rate": 0.95, "pitch": 0.9}
        }
        voice_params = persona_map.get(req.persona, {"rate": 1.0, "pitch": 1.0})
        instructions = {
            "text": req.text,
            "persona": req.persona,
            "emotion": req.emotion,
            "audio_format": req.audio_format,
            "voice_parameters": {"rate": req.rate or voice_params["rate"], "pitch": req.pitch or voice_params["pitch"]}
        }
        return {"use_client_tts": True, "tts_instructions": instructions}

    # Check cache
    cached = get_cached(req.text, req.persona, req.emotion, req.audio_format, req.pitch, req.rate)
    if cached:
        return {"audio_url": cached["audio_url"], "duration_ms": cached["duration_ms"], "voice_parameters_used": cached["voice_parameters_used"]}

    provider = get_provider()
    res = await provider.generate(req.session_id, req.text, req.persona, req.emotion, req.audio_format, req.pitch, req.rate)
    set_cached(req.text, req.persona, req.emotion, req.audio_format, req.pitch, req.rate, res)
    return {"audio_url": res["audio_url"], "duration_ms": res["duration_ms"], "voice_parameters_used": res["voice_parameters_used"]}

# Minimal WebSocket streaming endpoint for TTS playback
@router.websocket("/ws/{session_id}")
async def ws_tts(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") == "generate":
                text = msg.get("text")
                persona = msg.get("persona", "neutral")
                emotion = msg.get("emotion")
                audio_format = msg.get("audio_format", "wav")
                pitch = msg.get("pitch")
                rate = msg.get("rate")
                provider = get_provider()
                res = await provider.generate(session_id, text, persona, emotion, audio_format, pitch, rate)
                # Stream simulated small chunks (base64) then send completed flag
                b64 = res.get("audio_b64")
                # break into small chunks
                chunk_size = 200
                for i in range(0, len(b64), chunk_size):
                    chunk = b64[i:i+chunk_size]
                    await websocket.send_json({"type":"audio_chunk","data": chunk})
                await websocket.send_json({"type":"complete","audio_url": res.get("audio_url"), "duration_ms": res.get("duration_ms")})
            else:
                await websocket.send_json({"type":"error","message":"unknown message type"})
    except WebSocketDisconnect:
        return
