"""Simple in-memory cache for TTS artifacts. Replace with Redis or CDN in production."""

_cache: dict = {}

from ..core.config import settings

_redis = None
if settings.REDIS_URL:
    try:
        import redis
        _redis = redis.Redis.from_url(settings.REDIS_URL)
    except Exception:
        _redis = None


def _make_key(text: str, persona: str, emotion: str | None, audio_format: str, pitch: float | None, rate: float | None) -> str:
    return f"tts:{hash((text, persona, emotion, audio_format, pitch, rate))}"


def get_cached(text: str, persona: str, emotion: str | None, audio_format: str, pitch: float | None, rate: float | None):
    key = _make_key(text, persona, emotion, audio_format, pitch, rate)
    if _redis:
        try:
            v = _redis.get(key)
            if v:
                import json
                return json.loads(v)
        except Exception:
            pass
    return _cache.get(key)


def set_cached(text: str, persona: str, emotion: str | None, audio_format: str, pitch: float | None, rate: float | None, value):
    key = _make_key(text, persona, emotion, audio_format, pitch, rate)
    if _redis:
        try:
            import json
            _redis.set(key, json.dumps(value))
            return key
        except Exception:
            pass
    _cache[key] = value
    return key
