import asyncio
from app.stt.mock_stt import MockSTT


async def run_mock():
    stt = MockSTT(session_id="s1")
    await stt.process_chunk("hello this is a test")
    await stt.process_chunk(" um I was nervous  but I fixed it")
    res = await stt.finalize()
    return res


def test_mock_stt_returns_timestamps():
    loop = asyncio.new_event_loop()
    res = loop.run_until_complete(run_mock())
    assert "transcript" in res
    assert isinstance(res["word_timestamps"], list)
    assert res["speech_rate_wpm"] > 0
    assert isinstance(res["filler_words"], list)
    loop.close()
