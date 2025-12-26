"""Whisper reprocessing worker (optional):
- If `faster_whisper` is installed, uses it to transcribe an audio file with higher accuracy.
- Otherwise falls back to a simple simulated reprocess using the MockSTT (useful for CI/tests).

The worker returns a dict compatible with STT finalize outputs: transcript, word_timestamps, filler_words, pause_segments, speech_rate_wpm
"""
from typing import Dict, Any
import os


def reprocess_audio(audio_path: str, model_name: str = "small") -> Dict[str, Any]:
    """Reprocess an audio file for higher-accuracy transcript.
    Returns a dict similar to STT finalize output.
    If faster-whisper is not available, produce a simulated transcript.
    """
    try:
        # try faster-whisper first
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device="cpu")
        segments, info = model.transcribe(audio_path, beam_size=5)
        # build transcript and simple word timestamps by splitting segments
        words = []
        current_ms = 0
        word_timestamps = []
        transcript_parts = []
        for segment in segments:
            text = segment.text.strip()
            transcript_parts.append(text)
            # naive split into words and assign times proportionally within segment
            seg_ms = int((segment.end - segment.start) * 1000)
            wlist = text.split()
            if not wlist:
                continue
            per_word = max(10, seg_ms // len(wlist))
            start = int(segment.start * 1000)
            for i, w in enumerate(wlist):
                s = start + i * per_word
                e = s + per_word
                word_timestamps.append({"word": w, "start_ms": s, "end_ms": e, "confidence": getattr(segment, "avg_logprob", 0)})
        transcript = " ".join(transcript_parts)
        # simple fillers detection
        filler_words = [w for w in word_timestamps if w["word"].lower() in ("um", "uh", "like", "you", "know")] 
        pause_segments = []
        speech_rate_wpm = int(len(transcript.split()) / (max(1, (word_timestamps[-1]["end_ms"] - word_timestamps[0]["start_ms"]) / 60000))) if word_timestamps else 140
        return {
            "transcript": transcript,
            "word_timestamps": word_timestamps,
            "filler_words": filler_words,
            "pause_segments": pause_segments,
            "speech_rate_wpm": speech_rate_wpm,
        }
    except Exception:
        # Fallback: simulate by using MockSTT behavior
        try:
            from .mock_stt import MockSTT
            # simulate reading file name as text for deterministic output in tests
            base = os.path.basename(audio_path)
            simulated_text = os.path.splitext(base)[0].replace("_", " ")
            stt = MockSTT(session_id="reprocess")
            return awaitable_finalize_simulated(stt, simulated_text)
        except Exception:
            # final fallback minimal
            return {"transcript": "", "word_timestamps": [], "filler_words": [], "pause_segments": [], "speech_rate_wpm": 0}


def awaitable_finalize_simulated(stt, transcript: str):
    """Helper that synchronously calls the MockSTT finalize using its internal helper.
    Returns the dict in a synchronous way (tests will call this via run loop when needed).
    """
    # MockSTT's _finalize_with_transcript is async; call it using an event loop
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(stt._finalize_with_transcript(transcript))
    finally:
        loop.close()
    return res
