"""Session store with optional Redis backing. Falls back to in-memory store when REDIS_URL not set.
"""
import json
import os
from typing import Any

from ..core.config import settings

_sessions: dict = {}

# Lazy import redis to avoid test-time overhead if not configured
_redis = None
if settings.REDIS_URL:
    try:
        import redis
        _redis = redis.Redis.from_url(settings.REDIS_URL)
    except Exception:
        _redis = None


def _redis_get(key: str):
    try:
        v = _redis.get(key)
        if not v:
            return None
        return json.loads(v)
    except Exception:
        return None


def _redis_set(key: str, val: Any):
    try:
        _redis.set(key, json.dumps(val))
        return True
    except Exception:
        return False


def create_session(session_id: str, data: dict) -> None:
    if _redis:
        _redis_set(f"session:{session_id}", data)
    else:
        _sessions[session_id] = data


def get_session(session_id: str) -> dict:
    if _redis:
        val = _redis_get(f"session:{session_id}")
        return val or {}
    return _sessions.get(session_id, {})


def set_session_field(session_id: str, key: str, value) -> None:
    if _redis:
        sess = _redis_get(f"session:{session_id}") or {}
        sess[key] = value
        _redis_set(f"session:{session_id}", sess)
    else:
        _sessions.setdefault(session_id, {})[key] = value


def delete_session(session_id: str) -> None:
    if _redis:
        try:
            _redis.delete(f"session:{session_id}")
        except Exception:
            pass
    else:
        _sessions.pop(session_id, None)
