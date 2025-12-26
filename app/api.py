from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .llm.agent import start_interview as llm_start
from .llm.agent import finalize_interview as llm_finalize

router = APIRouter()

from .state.session_store import create_session, get_session, set_session_field

class StartInterviewRequest(BaseModel):
    session_id: str
    user_id: str
    interview_type: str
    persona: str
    role_info: dict | None = None
    emotion_opt_in: bool | None = False
    client_tts: bool | None = False

class StartInterviewResponse(BaseModel):
    question_id: str
    question_text: str
    expected_topics: list[str] | None = None

@router.post("/sessions/start", response_model=StartInterviewResponse)
async def start_session(req: StartInterviewRequest):
    # Call LLM stub to get initial question
    res = await llm_start(
        session_id=req.session_id,
        user_id=req.user_id,
        interview_type=req.interview_type,
        persona=req.persona,
        role_info=req.role_info or {},
    )
    # Persist session metadata (in-memory store for MVP)
    create_session(req.session_id, {
        "user_id": req.user_id,
        "interview_type": req.interview_type,
        "persona": req.persona,
        "emotion_opt_in": bool(req.emotion_opt_in),
        "client_tts": bool(req.client_tts)
    })
    return res

class PreferenceUpdateRequest(BaseModel):
    emotion_opt_in: bool | None = None
    client_tts: bool | None = None

@router.patch("/sessions/{session_id}/preferences")
async def update_preferences(session_id: str, prefs: PreferenceUpdateRequest):
    # Update session-level preferences (in-memory store for MVP)
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    if prefs.emotion_opt_in is not None:
        set_session_field(session_id, "emotion_opt_in", bool(prefs.emotion_opt_in))
    if prefs.client_tts is not None:
        set_session_field(session_id, "client_tts", bool(prefs.client_tts))
    return {"status":"ok","session_id":session_id,"updated": {"emotion_opt_in": prefs.emotion_opt_in, "client_tts": prefs.client_tts}}

class FinalizeRequest(BaseModel):
    session_id: str
    include_example_improvements: bool | None = False
    # Optional: path to an audio file to run higher-accuracy reprocessing (Whisper)
    audio_path: str | None = None
    # Optional: remote audio URL that will be fetched to a temporary file for reprocessing
    audio_url: str | None = None

@router.post("/sessions/finalize")
async def finalize(req: FinalizeRequest):
    whisper_res = None
    local_tmp = None
    # If an audio_url is provided, fetch it to a temp file and reprocess
    if req.audio_url:
        try:
            from .stt.audio_fetcher import fetch_audio_to_temp
            local_tmp = fetch_audio_to_temp(req.audio_url)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Audio download failed; continuing without Whisper reprocessing")
            local_tmp = None

    # If an audio_path was provided, prefer it; else use downloaded tmp file
    target_audio = req.audio_path or local_tmp
    if target_audio:
        try:
            from .stt.whisper_worker import reprocess_audio
            whisper_res = reprocess_audio(target_audio)
        except Exception:
            # Non-fatal: log and continue with regular finalize
            import logging
            logging.getLogger(__name__).exception("Whisper reprocessing failed; continuing without it")
            whisper_res = None

    res = await llm_finalize(session_id=req.session_id, include_example_improvements=req.include_example_improvements, whisper_result=whisper_res)
    # Attach whisper result if available for transparency/provenance
    if whisper_res:
        res["whisper_reprocessed"] = True

    # Cleanup downloaded temp file if we created one
    if local_tmp:
        try:
            os.remove(local_tmp)
        except Exception:
            pass

    return res

@router.post("/annotations")
async def log_annotation(annotation: dict):
    # Placeholder - would persist in DB
    return {"status":"ok","annotation_received": True}
