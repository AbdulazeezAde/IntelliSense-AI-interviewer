from typing import Dict, Any
import uuid

async def start_interview(session_id: str, user_id: str, interview_type: str, persona: str, role_info: Dict[str,Any]):
    # Return a sample opening question
    qid = f"q-{uuid.uuid4().hex[:8]}"
    return {
        "question_id": qid,
        "question_text": "Tell me about a time you faced a difficult technical problem and how you solved it.",
        "expected_topics": ["situation","task","action","result"]
    }

async def generate_question(session_id: str, seed_question_id: str | None = None, purpose: str = "next", target_topics: list | None = None, difficulty: str = "medium"):
    qid = f"q-{uuid.uuid4().hex[:8]}"
    return {"question_id": qid, "question_text": "Can you expand on the technical tradeoffs you considered?", "suggested_pacing_seconds": 30}

async def process_answer(**kwargs):
    # Minimal stub: compute a naive score
    transcript = kwargs.get("transcript","")
    filler_count = len(kwargs.get("filler_words",[]))
    speech_rate = kwargs.get("speech_rate_wpm",140)
    # naive scoring
    content = 80 if len(transcript.split())>10 else 50
    structure = 75 if "result" in transcript.lower() or "finally" in transcript.lower() else 60
    delivery = max(0, 100 - (abs(speech_rate-130)))
    confidence = 60
    overall = int((content*0.4 + structure*0.2 + delivery*0.2 + confidence*0.2))
    return {
        "turn_score": overall,
        "component_scores":{
            "content":content,
            "structure":structure,
            "delivery":delivery,
            "conciseness":70,
            "confidence":confidence
        },
        "explanations":{
            "content":"Covered key aspects." if content>70 else "Partial coverage, add more specifics.",
            "structure":"Structure present." if structure>70 else "Add STAR structure.",
            "delivery":f"Speech rate {speech_rate} WPM; {filler_count} filler words detected.",
            "confidence":"Emotion analysis not enabled in this stub."
        },
        "action":"CONTINUE",
        "follow_up_question": None,
        "short_feedback_snippet":"Good start; consider adding concrete metrics."
    }

async def finalize_interview(session_id: str, include_example_improvements: bool=False, **kwargs):
    # Minimal aggregate summary
    res = {
        "overall_score":78,
        "component_breakdown":{
            "content":78,
            "structure":74,
            "delivery":76,
            "confidence":60
        },
        "strengths":["Clear storytelling","Concise outcomes"],
        "weaknesses":["Add more technical specificity","Reduce filler words"],
        "emotion_insights":[],
        "improvement_plan":[{"task_id":"t1","task":"Practice STAR on 3 past projects"}],
        "example_improved_answers": []
    }
    # If whisper reprocessing result is provided, include it for provenance and optionally adjust summary
    whisper = kwargs.get("whisper_result")
    if whisper:
        res["whisper_result"] = whisper
        res["note"] = "A higher-accuracy transcript was produced by Whisper reprocessing."
    return res
