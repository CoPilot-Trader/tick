"""
Vector Store for Embeddings

This module provides vector storage and similarity search for semantic caching.
Uses in-memory storage for testing, can be extended to use Redis or other vector DBs.

Why Vector Store?
- Fast similarity search
- Efficient storage of embeddings
- Scalable to millions of vectors
- Can be replaced with production vector DB (Pinecone, Weaviate, etc.)
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime


class VectorStore:
    """
    In-memory vector store for embeddings.
    
    Stores article embeddings and allows similarity search.
    For production, this can be replaced with Redis, Pinecone, or Weaviate.
    
    Example:
        store = VectorStore()
        store.add(article_id="article_123", embedding=[0.1, 0.2, ...], metadata={...})
        similar = store.search(query_embedding=[0.1, 0.2, ...], top_k=5)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize vector store.
        
        Args:
            config: Optional configuration:
                   - similarity_threshold: Minimum similarity for matches (default: 0.85)
        """
        self.config = config or {}
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)
        
        # In-memory storage
        self._embeddings: Dict[str, np.ndarray] = {}  # article_id -> embedding
        self._metadata: Dict[str, Dict[str, Any]] = {}  # article_id -> metadata
    
    def add(self, article_id: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an embedding to the store.
        
        Args:
            article_id: Unique identifier for the article
            embedding: Vector embedding (list of floats)
            metadata: Optional metadata (sentiment score, timestamp, etc.)
        
        Example:
            store.add("article_123", [0.1, 0.2, 0.3], {"sentiment_score": 0.75})
        """
        self._embeddings[article_id] = np.array(embedding, dtype=np.float32)
        self._metadata[article_id] = metadata or {}
        self._metadata[article_id]["added_at"] = datetime.utcnow().isoformat() + "Z"
    
    def get(self, article_id: str) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Get embedding and metadata for an article.
        
        Args:
            article_id: Article identifier
        
        Returns:
            Tuple of (embedding, metadata) or None if not found
        
        Example:
            embedding, metadata = store.get("article_123")
        """
        if article_id not in self._embeddings:
            return None
        
        return self._embeddings[article_id], self._metadata[article_id]
    
    def search(self, query_embedding: List[float], top_k: int = 5, threshold: Optional[float] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar embeddings using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            threshold: Minimum similarity threshold (default: from config)
        
        Returns:
            List of tuples: (article_id, similarity_score, metadata)
            Sorted by similarity (highest first)
        
        Example:
            results = store.search([0.1, 0.2, 0.3], top_k=5)
            # Returns: [("article_123", 0.92, {...}), ("article_456", 0.88, {...}), ...]
        """
        if not self._embeddings:
            return []
        
        if threshold is None:
            threshold = self.similarity_threshold
        
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)  # Normalize
        
        similarities = []
        for article_id, embedding in self._embeddings.items():
            # Normalize embedding
            norm_embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            # Calculate cosine similarity
            similarity = np.dot(query_vec, norm_embedding)
            
            if similarity >= threshold:
                similarities.append((
                    article_id,
                    float(similarity),
                    self._metadata[article_id]
                ))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return similarities[:top_k]
    
    def delete(self, article_id: str) -> bool:
        """
        Delete an embedding from the store.
        
        Args:
            article_id: Article identifier
        
        Returns:
            True if deleted, False if not found
        
        Example:
            deleted = store.delete("article_123")
        """
        if article_id in self._embeddings:
            del self._embeddings[article_id]
            del self._metadata[article_id]
            return True
        return False
    
    def count(self) -> int:
        """
        Get total number of embeddings in store.
        
        Returns:
            Number of stored embeddings
        
        Example:
            count = store.count()
        """
        return len(self._embeddings)
    
    def clear(self) -> None:
        """Clear all embeddings from store."""
        self._embeddings.clear()
        self._metadata.clear()

