from typing import Dict, Any, List

# Default weights (can be overridden per interview type)
DEFAULT_WEIGHTS = {
    "content": 0.40,
    "structure": 0.20,
    "delivery": 0.15,
    "conciseness": 0.10,
    "confidence": 0.10,
    "technical": 0.05
}


def _topic_match_score(transcript: str, expected_topics: List[str]) -> int:
    if not expected_topics:
        return 70
    t = transcript.lower()
    matches = sum(1 for topic in expected_topics if topic.lower() in t)
    return int(100 * matches / max(1, len(expected_topics)))


def _filler_penalty(filler_words: List[Dict[str, Any]]) -> int:
    # return penalty to delivery based on count
    n = len(filler_words or [])
    if n == 0:
        return 0
    # small penalty for each filler
    return min(30, n * 5)


def _pause_penalty(pause_segments: List[Dict[str, Any]]) -> int:
    # too many or too long pauses hurt delivery/conciseness
    if not pause_segments:
        return 0
    total = sum((p.get("end_ms",0)-p.get("start_ms",0)) for p in pause_segments)
    # penalty up to 20 points
    secs = total / 1000.0
    return min(20, int(secs * 2))


def _speech_rate_score(wpm: int) -> int:
    # optimal WPM range [110,160]
    if wpm is None:
        return 70
    if wpm < 80:
        return max(0, 50 + int((wpm - 80) * 0.5))
    if 110 <= wpm <= 160:
        return 100
    if wpm > 200:
        return 40
    # linear degrade between 160 and 200
    if wpm > 160:
        return max(40, 100 - int((wpm - 160) * 1.5))
    # between 80 and 110
    return 80


def compute_turn_score(component_scores: Dict[str, float],
                       stt_metrics: Dict[str, Any] | None = None,
                       expected_topics: List[str] | None = None,
                       emotion_events: List[Dict[str, Any]] | None = None,
                       weights: Dict[str, float] | None = None) -> Dict[str, Any]:
    """Compute refined turn score using component scores and STT/emotion signals.
    Returns detailed explanation/provenance for each component.
    """
    w = weights or DEFAULT_WEIGHTS
    stt = stt_metrics or {}
    filler_words = stt.get("filler_words", [])
    pause_segments = stt.get("pause_segments", [])
    wpm = stt.get("speech_rate_wpm")
    transcript = stt.get("transcript", "")

    # compute derived metrics
    topic_score = _topic_match_score(transcript, expected_topics or [])
    filler_pen = _filler_penalty(filler_words)
    pause_pen = _pause_penalty(pause_segments)
    speech_rate = _speech_rate_score(wpm)

    # Merge with existing component_scores as baseline
    baseline = {k: float(v) for k, v in (component_scores or {}).items()}

    # Start building refinements and provenance
    details = {}

    # Content: combine baseline content and topic matching
    content_base = baseline.get("content", 70)
    content_final = int((content_base * 0.7) + (topic_score * 0.3))
    details["content"] = {
        "score": content_final,
        "evidence": {
            "content_base": content_base,
            "topic_match": topic_score,
            "matched_topics": expected_topics or []
        },
        "weight": w.get("content", 0.4)
    }

    # Structure: baseline + heuristic for STAR presence
    structure_base = baseline.get("structure", 70)
    # Heuristic: presence of words indicating STAR
    st = transcript.lower()
    star_bonus = 10 if ("situation" in st or "action" in st or "result" in st or "task" in st or "finally" in st) else 0
    structure_final = min(100, int(structure_base + star_bonus))
    details["structure"] = {"score": structure_final, "evidence": {"structure_base": structure_base, "star_bonus": star_bonus}, "weight": w.get("structure", 0.2)}

    # Delivery: baseline minus penalties from fillers/pauses + speech_rate
    delivery_base = baseline.get("delivery", 70)
    delivery_pen = filler_pen + pause_pen
    delivery_final = max(0, min(100, int((delivery_base + speech_rate) / 2 - delivery_pen)))
    details["delivery"] = {"score": delivery_final, "evidence": {"delivery_base": delivery_base, "speech_rate_score": speech_rate, "filler_penalty": filler_pen, "pause_penalty": pause_pen}, "weight": w.get("delivery", 0.15)}

    # Conciseness: baseline penalized by pause and filler density
    conc_base = baseline.get("conciseness", 70)
    conc_final = max(0, conc_base - int((len(filler_words) * 2) + pause_pen/2))
    details["conciseness"] = {"score": conc_final, "evidence": {"conciseness_base": conc_base, "filler_count": len(filler_words), "pause_penalty": pause_pen}, "weight": w.get("conciseness", 0.1)}

    # Confidence: derived from emotion events conservatively
    conf_base = baseline.get("confidence", 60)
    # if emotion events indicate stress, reduce confidence slightly
    stress_events = [e for e in (emotion_events or []) if e.get("label") == "stress"]
    stress_pen = int(min(20, sum(e.get("score",0) for e in stress_events) * 10))
    conf_final = max(0, conf_base - stress_pen)
    details["confidence"] = {"score": conf_final, "evidence": {"confidence_base": conf_base, "stress_penalty": stress_pen, "stress_events": stress_events}, "weight": w.get("confidence", 0.1)}

    # Technical: keep baseline or increase if technical keywords present
    tech_base = baseline.get("technical", 70)
    tech_bonus = 10 if any(k in transcript.lower() for k in ["latency","throughput","scalab","optimiz","algorithm","complexity"]) else 0
    tech_final = min(100, tech_base + tech_bonus)
    details["technical"] = {"score": tech_final, "evidence": {"technical_base": tech_base, "tech_bonus": tech_bonus}, "weight": w.get("technical", 0.05)}

    # Aggregate weighted sum
    total = 0.0
    for k, v in details.items():
        total += v["score"] * v["weight"]

    overall = int(total)

    # Attach provenance and raw metrics
    result = {
        "overall": overall,
        "details": details,
        "provenance": {
            "filler_count": len(filler_words),
            "pause_total_ms": sum((p.get("end_ms",0)-p.get("start_ms",0)) for p in pause_segments),
            "speech_rate_wpm": wpm,
            "topic_score": topic_score
        }
    }
    return result
