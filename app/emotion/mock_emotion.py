from typing import List, Dict

async def analyze_audio_fragment(audio_bytes: bytes) -> List[Dict]:
    # Very small stub: return no emotions by default
    return []

async def analyze_transcript(transcript: str) -> List[Dict]:
    # heuristic: if 'nervous' appears, return a stress event
    events = []
    if "nervous" in transcript.lower():
        events.append({"label":"stress","score":0.7,"start_ms":0,"end_ms":1000})
    return events
