"""
Tests for middleware components (auth, rate limiting, caching).
"""

import os
import pytest
from api.middleware.auth import _get_valid_keys, _is_auth_enabled
from api.middleware.response_cache import cache_key, cache_get, cache_set


class TestAuth:
    def test_auth_disabled_by_default(self):
        os.environ.pop("TICK_AUTH_ENABLED", None)
        assert _is_auth_enabled() is False

    def test_auth_enabled_via_env(self):
        os.environ["TICK_AUTH_ENABLED"] = "true"
        assert _is_auth_enabled() is True
        os.environ["TICK_AUTH_ENABLED"] = "false"

    def test_default_key_generated(self):
        os.environ.pop("TICK_API_KEYS", None)
        keys = _get_valid_keys()
        assert len(keys) == 1

    def test_custom_keys_from_env(self):
        os.environ["TICK_API_KEYS"] = "key1,key2,key3"
        keys = _get_valid_keys()
        assert keys == {"key1", "key2", "key3"}
        os.environ.pop("TICK_API_KEYS")

    def test_empty_keys_use_default(self):
        os.environ["TICK_API_KEYS"] = ""
        keys = _get_valid_keys()
        assert len(keys) == 1
        os.environ.pop("TICK_API_KEYS")


class TestResponseCache:
    def test_cache_key_deterministic(self):
        k1 = cache_key("test", a=1, b=2)
        k2 = cache_key("test", a=1, b=2)
        assert k1 == k2

    def test_cache_key_different_params(self):
        k1 = cache_key("test", a=1)
        k2 = cache_key("test", a=2)
        assert k1 != k2

    def test_cache_set_and_get(self):
        cache_set("test:unit", {"value": 42}, ttl_seconds=60)
        result = cache_get("test:unit")
        assert result == {"value": 42}

    def test_cache_miss(self):
        result = cache_get("nonexistent:key")
        assert result is None

    def test_cache_ttl_expiry(self):
        import time
        cache_set("test:expire", {"temp": True}, ttl_seconds=1)
        result = cache_get("test:expire")
        assert result is not None
        time.sleep(1.1)
        result = cache_get("test:expire")
        assert result is None
