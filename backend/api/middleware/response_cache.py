"""
Simple response cache using Redis or in-memory fallback.

Caches JSON API responses with configurable TTL per endpoint.
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

_cache: Dict[str, tuple] = {}  # key -> (value, expire_time)


def _get_redis():
    """Try to get a Redis connection."""
    try:
        import redis
        import os
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(url, decode_responses=True, socket_timeout=2)
        client.ping()
        return client
    except Exception:
        return None


_redis_client = None
_redis_checked = False


def _redis():
    global _redis_client, _redis_checked
    if not _redis_checked:
        _redis_client = _get_redis()
        _redis_checked = True
    return _redis_client


def cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from prefix and kwargs."""
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"tick:{prefix}:{h}"


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache (Redis first, then memory)."""
    r = _redis()
    if r:
        try:
            val = r.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass

    import time
    if key in _cache:
        val, exp = _cache[key]
        if exp > time.time():
            return val
        del _cache[key]
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 60):
    """Set value in cache with TTL."""
    r = _redis()
    if r:
        try:
            r.setex(key, ttl_seconds, json.dumps(value, default=str))
            return
        except Exception:
            pass

    import time
    _cache[key] = (value, time.time() + ttl_seconds)
