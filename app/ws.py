from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import uuid
import logging

from .stt.mock_stt import MockSTT
from .llm.agent import process_answer
from .emotion.mock_emotion import analyze_transcript
from .scoring.engine import compute_turn_score

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple in-memory mapping for demo purposes
connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/audio/{session_id}")
async def audio_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    connections[session_id] = websocket
    # Use pluggable STT provider (prefer VOSK if available, else fall back to mock)
    from .stt.provider import MockSTTProvider, VoskSTTProvider
    try:
        stt = VoskSTTProvider(session_id=session_id)
    except Exception:
        stt = MockSTTProvider(session_id=session_id)
    try:
        while True:
            msg = await websocket.receive_json()
            # Expect messages like {"type":"audio_chunk","data":"<base64>"} or {"type":"finalize"}
            mtype = msg.get("type")
            if mtype == "audio_chunk":
                chunk = msg.get("data")
                await stt.process_chunk(chunk)
                # Optionally return a partial transcript
                partial = stt.get_partial()
                if partial:
                    await websocket.send_json({"type":"stt_partial","partial":partial})

            elif mtype == "finalize":
                # Finalize STT, run emotion analysis, invoke LLM scoring
                stt_result = await stt.finalize()
                transcript = stt_result.get("transcript", "")
                # Minimal turn id for traceability
                turn_id = f"t-{uuid.uuid4().hex[:8]}"
                # Check session opt-in for emotion analysis
                from .state.session_store import get_session
                sess = get_session(session_id)
                emotion_events = []
                if sess.get("emotion_opt_in"):
                    try:
                        emotion_events = await analyze_transcript(transcript)
                    except Exception:
                        logger.exception("Emotion analysis failed; continuing without it")
                        emotion_events = []
                else:
                    # advisory note: emotion analysis skipped due to opt-out
                    emotion_events = []

                # Call LLM agent to process answer
                try:
                    llm_result = await process_answer(
                        session_id=session_id,
                        turn_id=turn_id,
                        transcript=transcript,
                        word_timestamps=stt_result.get("word_timestamps", []),
                        filler_words=stt_result.get("filler_words", []),
                        pause_segments=stt_result.get("pause_segments", []),
                        speech_rate_wpm=stt_result.get("speech_rate_wpm", 140),
                        audio_quality=stt_result.get("audio_quality", {}),
                        emotion_events=emotion_events,
                        question_id=msg.get("question_id")
                    )
                except Exception:
                    logger.exception("LLM processing failed")
                    await websocket.send_json({"type":"error","message":"LLM processing failed"})
                    continue

                # Optionally refine via scoring engine using STT metrics, expected topics, and emotion events
                try:
                    scoring = compute_turn_score(
                        llm_result.get("component_scores", {}),
                        stt_metrics=stt_result,
                        expected_topics=msg.get("expected_topics") or [],
                        emotion_events=emotion_events,
                    )
                except Exception:
                    logger.exception("Scoring engine failed; returning LLM result only")
                    scoring = {}

                response = {
                    "turn_id": turn_id,
                    "stt": stt_result,
                    "emotion_events": emotion_events,
                    "llm": llm_result,
                    "scoring": scoring
                }
                await websocket.send_json({"type":"turn_result","result":response})

            elif mtype == "sim_transcript":
                # Shortcut for local testing: send a simulated final transcript
                transcript = msg.get("transcript")
                # build a fake STT result and reuse the finalize path
                stt_result = await stt._finalize_with_transcript(transcript)
                turn_id = f"t-{uuid.uuid4().hex[:8]}"
                # Respect session opt-in for emotion analysis
                from .state.session_store import get_session
                sess = get_session(session_id)
                emotion_events = []
                if sess.get("emotion_opt_in"):
                    try:
                        emotion_events = await analyze_transcript(transcript)
                    except Exception:
                        logger.exception("Emotion analysis failed; continuing without it")
                        emotion_events = []
                llm_result = await process_answer(
                    session_id=session_id,
                    turn_id=turn_id,
                    transcript=transcript,
                    word_timestamps=stt_result.get("word_timestamps", []),
                    filler_words=stt_result.get("filler_words", []),
                    pause_segments=stt_result.get("pause_segments", []),
                    speech_rate_wpm=stt_result.get("speech_rate_wpm", 140),
                    audio_quality=stt_result.get("audio_quality", {}),
                    emotion_events=emotion_events,
                    question_id=msg.get("question_id")
                )
                scoring = compute_turn_score(llm_result.get("component_scores", {}))
                response = {
                    "turn_id": turn_id,
                    "stt": stt_result,
                    "emotion_events": emotion_events,
                    "llm": llm_result,
                    "scoring": scoring
                }
                await websocket.send_json({"type":"turn_result","result":response})
            else:
                await websocket.send_json({"type":"error","message":"unknown message type"})
    except WebSocketDisconnect:
        connections.pop(session_id, None)
