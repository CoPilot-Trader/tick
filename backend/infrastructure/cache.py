"""
Redis cache wrapper for TICK.
Used for feature caching in the inference pipeline.
"""

import json
import logging
from typing import Optional, Dict, Any, Union
from datetime import timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .config import settings

logger = logging.getLogger(__name__)


class Cache:
    """
    Redis cache wrapper for TICK.
    Provides feature caching for the inference pipeline.
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._client: Optional[Any] = None
        self._connected = False
        
        # In-memory fallback when Redis is unavailable
        self._memory_cache: Dict[str, Any] = {}
    
    def connect(self) -> bool:
        """Establish Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("redis package not installed. Using in-memory cache fallback.")
            return False
        
        try:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self._client.ping()
            self._connected = True
            logger.info("Redis connection established")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
            self._connected = False
            return False
    
    def disconnect(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Redis connection closed")
    
    def _get_key(self, prefix: str, *parts) -> str:
        """Generate a cache key from parts."""
        return f"{prefix}:{':'.join(str(p) for p in parts)}"
    
    # =========================================================================
    # Basic Operations
    # =========================================================================
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = None,
        prefix: str = "tick"
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time-to-live in seconds (None for no expiry)
            prefix: Key prefix for namespacing
        """
        full_key = self._get_key(prefix, key)
        serialized = json.dumps(value) if not isinstance(value, str) else value
        
        if self._connected and self._client:
            try:
                if ttl_seconds:
                    self._client.setex(full_key, ttl_seconds, serialized)
                else:
                    self._client.set(full_key, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to in-memory
        self._memory_cache[full_key] = {
            "value": serialized,
            "ttl": ttl_seconds
        }
        return True
    
    def get(self, key: str, prefix: str = "tick") -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            prefix: Key prefix for namespacing
            
        Returns:
            Cached value (JSON deserialized) or None if not found
        """
        full_key = self._get_key(prefix, key)
        
        if self._connected and self._client:
            try:
                value = self._client.get(full_key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                return None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to in-memory
        cached = self._memory_cache.get(full_key)
        if cached:
            try:
                return json.loads(cached["value"])
            except json.JSONDecodeError:
                return cached["value"]
        return None
    
    def delete(self, key: str, prefix: str = "tick") -> bool:
        """Delete a key from cache."""
        full_key = self._get_key(prefix, key)
        
        if self._connected and self._client:
            try:
                self._client.delete(full_key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        # Fallback to in-memory
        self._memory_cache.pop(full_key, None)
        return True
    
    def exists(self, key: str, prefix: str = "tick") -> bool:
        """Check if a key exists in cache."""
        full_key = self._get_key(prefix, key)
        
        if self._connected and self._client:
            try:
                return self._client.exists(full_key) > 0
            except Exception as e:
                logger.error(f"Redis exists error: {e}")
        
        return full_key in self._memory_cache
    
    # =========================================================================
    # Feature-specific Operations
    # =========================================================================
    
    def set_features(
        self,
        ticker: str,
        timeframe: str,
        features: Dict[str, float],
        ttl_seconds: int = None
    ) -> bool:
        """
        Cache calculated features for a ticker.
        
        Args:
            ticker: Stock symbol
            timeframe: Data timeframe
            features: Dictionary of feature name -> value
            ttl_seconds: Cache TTL (defaults to settings.feature_cache_ttl)
        """
        key = f"features:{ticker}:{timeframe}"
        ttl = ttl_seconds or settings.feature_cache_ttl
        return self.set(key, features, ttl_seconds=ttl)
    
    def get_features(self, ticker: str, timeframe: str) -> Optional[Dict[str, float]]:
        """
        Get cached features for a ticker.
        
        Args:
            ticker: Stock symbol
            timeframe: Data timeframe
            
        Returns:
            Dictionary of features or None if not cached
        """
        key = f"features:{ticker}:{timeframe}"
        return self.get(key)
    
    def set_latest_bar(
        self,
        ticker: str,
        timeframe: str,
        bar: Dict[str, Any],
        ttl_seconds: int = 60
    ) -> bool:
        """Cache the latest OHLCV bar."""
        key = f"latest_bar:{ticker}:{timeframe}"
        return self.set(key, bar, ttl_seconds=ttl_seconds)
    
    def get_latest_bar(self, ticker: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get cached latest bar."""
        key = f"latest_bar:{ticker}:{timeframe}"
        return self.get(key)
    
    # =========================================================================
    # Health Check
    # =========================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache health."""
        if not REDIS_AVAILABLE:
            return {
                "status": "fallback",
                "backend": "memory",
                "reason": "redis package not installed"
            }
        
        if not self._connected:
            return {
                "status": "fallback",
                "backend": "memory",
                "reason": "Redis not connected"
            }
        
        try:
            self._client.ping()
            info = self._client.info("memory")
            return {
                "status": "healthy",
                "backend": "redis",
                "used_memory": info.get("used_memory_human", "unknown")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "redis",
                "error": str(e)
            }
    
    def clear_all(self, prefix: str = "tick") -> int:
        """Clear all keys with the given prefix."""
        if self._connected and self._client:
            try:
                keys = self._client.keys(f"{prefix}:*")
                if keys:
                    return self._client.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        # Fallback: clear in-memory cache
        keys_to_delete = [k for k in self._memory_cache if k.startswith(f"{prefix}:")]
        for k in keys_to_delete:
            del self._memory_cache[k]
        return len(keys_to_delete)


# Global cache instance
_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
