from app.tts.cache import set_cached, get_cached


def test_tts_cache_set_get():
    text = "Hello persistence"
    persona = "neutral"
    val = {"audio_url":"/tmp/1.wav","duration_ms":123}
    set_cached(text, persona, None, "wav", None, None, val)
    got = get_cached(text, persona, None, "wav", None, None)
    assert got == val
