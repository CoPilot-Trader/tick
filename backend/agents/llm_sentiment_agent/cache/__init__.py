"""
Semantic Cache Package

This package contains semantic caching implementation for reducing GPT-4 API costs.

Components:
- SemanticCache: Semantic similarity detection using Sentence Transformers
- CacheManager: Cache storage and retrieval
- VectorStore: Vector database operations for embeddings

Why this package exists:
- Reduces API costs by caching similar articles
- Improves response time for cached queries
- Separates caching logic from main agent
- Makes it easy to switch cache backends (in-memory, Redis, etc.)
"""

from .semantic_cache import SemanticCache
from .cache_manager import CacheManager
from .vector_store import VectorStore

__all__ = [
    "SemanticCache",
    "CacheManager",
    "VectorStore",
]

