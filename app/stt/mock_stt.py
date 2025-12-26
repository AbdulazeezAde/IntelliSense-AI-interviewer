import asyncio
from typing import List, Dict

class MockSTT:
    """A simple mock STT to simulate streaming behavior and metadata.
    For real deployment, replace with a streaming STT provider integration.
    This enhanced mock estimates word timestamps and pause segments for better scoring.
    """
    FILLERS = {"um","uh","like","you","know","you know"}

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.chunks: List[str] = []
        self.partial = ""

    async def process_chunk(self, base64_chunk: str):
        # Simulate processing time
        await asyncio.sleep(0.005)
        # For demo, treat chunk as plaintext chunk
        self.chunks.append(base64_chunk)
        # Update partial transcript (simple join)
        self.partial = " ".join(self.chunks[-3:])

    def get_partial(self) -> str:
        return self.partial

    async def finalize(self) -> Dict:
        # Simulate final recognition
        transcript = " ".join(self.chunks)
        return await self._finalize_with_transcript(transcript)

    async def _finalize_with_transcript(self, transcript: str) -> Dict:
        words = transcript.split()
        word_timestamps = []
        # Simple time model: assume 150 WPM => ~400ms per word
        ms_per_word = 400
        current = 0
        fillers = []
        pause_segments = []
        last_word_time = 0
        for w in words:
            start = current
            end = current + ms_per_word
            wt = {"word": w, "start_ms": start, "end_ms": end, "confidence": 0.98}
            word_timestamps.append(wt)
            if w.lower().strip() in self.FILLERS:
                fillers.append({"word": w, "start_ms": start, "end_ms": end})
            current = end
            last_word_time = end
        # naive pause detection: if there is a double-space in transcript, mark a pause
        pause_segments = []
        if "  " in transcript:
            # find indices of double spaces and estimate pause positions
            idx = transcript.index("  ")
            # estimate pause around the nearest word
            pause_segments.append({"start_ms": max(0, int(idx/5)*ms_per_word), "end_ms": max(0, int(idx/5)*ms_per_word)+500})
        speech_rate_wpm = int(len(words) / (max(1, last_word_time) / 60000)) if last_word_time > 0 else 140
        return {
            "transcript": transcript,
            "word_timestamps": word_timestamps,
            "filler_words": fillers,
            "pause_segments": pause_segments,
            "speech_rate_wpm": speech_rate_wpm,
            "audio_quality": {"snr_db": 40.0, "clipping_ratio": 0.0}
        }
