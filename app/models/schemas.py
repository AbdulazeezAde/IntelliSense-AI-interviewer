from pydantic import BaseModel
from typing import List, Dict, Any

class WordTimestamp(BaseModel):
    word: str
    start_ms: int
    end_ms: int
    confidence: float

class EmotionEvent(BaseModel):
    label: str
    score: float
    start_ms: int
    end_ms: int

class ProcessAnswerRequest(BaseModel):
    session_id: str
    turn_id: str
    transcript: str
    word_timestamps: List[WordTimestamp] | None = None
    filler_words: List[Dict[str, Any]] | None = None
    pause_segments: List[Dict[str, Any]] | None = None
    speech_rate_wpm: int | None = None
    audio_quality: Dict[str, Any] | None = None
    emotion_events: List[EmotionEvent] | None = None
    question_id: str | None = None
    expected_topics: List[str] | None = None
