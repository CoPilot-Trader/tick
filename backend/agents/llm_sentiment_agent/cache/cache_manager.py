"""
Cache Manager

This module provides high-level cache management for sentiment analysis.
Coordinates between semantic cache and storage backend.

Why Cache Manager?
- Abstracts cache operations
- Handles cache invalidation
- Manages cache statistics
- Can switch between different storage backends
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .semantic_cache import SemanticCache

logger = logging.getLogger(__name__)


class CacheManager:
    """
    High-level cache manager for sentiment analysis.
    
    Manages semantic cache operations and provides statistics.
    
    Example:
        manager = CacheManager()
        cached = manager.get_cached_sentiment(article, "AAPL")
        if not cached:
            result = analyze_with_gpt4(article)
            manager.store_sentiment(article, result, "AAPL")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache manager.
        
        Args:
            config: Optional configuration:
                   - similarity_threshold: Minimum similarity for cache hit (default: 0.85)
                   - cache_ttl: Cache time-to-live in seconds (default: None)
                   - enable_cache: Enable caching (default: True)
        """
        self.config = config or {}
        self.enable_cache = self.config.get("enable_cache", True)
        self.cache_ttl = self.config.get("cache_ttl")
        
        # Initialize semantic cache
        self.semantic_cache: Optional[SemanticCache] = None
        if self.enable_cache:
            try:
                self.semantic_cache = SemanticCache(config={
                    "similarity_threshold": self.config.get("similarity_threshold", 0.85),
                    "cache_ttl": self.cache_ttl
                })
            except ImportError:
                # sentence-transformers not installed, disable cache
                logger.warning("sentence-transformers not installed. Disabling semantic cache.")
                self.enable_cache = False
                self.semantic_cache = None
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
    
    def get_cached_sentiment(self, article: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached sentiment for an article.
        
        Args:
            article: News article dictionary
            symbol: Stock symbol
        
        Returns:
            Cached sentiment result if found, None otherwise
        
        Example:
            cached = manager.get_cached_sentiment(article, "AAPL")
        """
        if not self.enable_cache or not self.semantic_cache:
            return None
        
        self._stats["total_requests"] += 1
        
        cached_result = self.semantic_cache.get_similar(article, symbol)
        
        if cached_result:
            self._stats["hits"] += 1
            return cached_result
        else:
            self._stats["misses"] += 1
            return None
    
    def store_sentiment(self, article: Dict[str, Any], sentiment_result: Dict[str, Any], symbol: str) -> None:
        """
        Store sentiment result in cache.
        
        Args:
            article: News article dictionary
            sentiment_result: Sentiment analysis result
            symbol: Stock symbol
        
        Example:
            manager.store_sentiment(article, sentiment_result, "AAPL")
        """
        if not self.enable_cache or not self.semantic_cache:
            return
        
        self.semantic_cache.store(article, sentiment_result, symbol)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats:
            {
                "hits": int,
                "misses": int,
                "total_requests": int,
                "hit_rate": float,
                "cache_info": dict
            }
        
        Example:
            stats = manager.get_stats()
            print(f"Cache hit rate: {stats['hit_rate']:.2%}")
        """
        stats = self._stats.copy()
        
        # Calculate hit rate
        if stats["total_requests"] > 0:
            stats["hit_rate"] = stats["hits"] / stats["total_requests"]
        else:
            stats["hit_rate"] = 0.0
        
        # Add semantic cache stats
        if self.semantic_cache:
            cache_info = self.semantic_cache.get_stats()
            stats["cache_info"] = cache_info
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear all cached entries."""
        if self.semantic_cache:
            self.semantic_cache.clear()
        
        # Reset statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
    
    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.enable_cache

