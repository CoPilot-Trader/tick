"""
Semantic Cache for Sentiment Analysis

This module provides semantic caching using Sentence Transformers to detect
similar articles and reuse sentiment analysis results.

Why Semantic Caching?
- Reduces GPT-4 API costs by 60%+ (target)
- Improves response time for cached queries
- Handles similar but not identical articles
- Uses embeddings to find semantic similarity
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np


class SemanticCache:
    """
    Semantic cache for sentiment analysis results.
    
    Uses Sentence Transformers to generate embeddings and find similar articles.
    If a similar article has been analyzed before, returns cached sentiment.
    
    Example:
        cache = SemanticCache()
        cached_result = cache.get_similar(article, "AAPL")
        if cached_result:
            return cached_result  # Use cached sentiment
        else:
            # Analyze with GPT-4 and cache result
            result = analyze_with_gpt4(article)
            cache.store(article, result)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize semantic cache.
        
        Args:
            config: Optional configuration:
                   - similarity_threshold: Minimum similarity for cache hit (default: 0.85)
                   - model_name: Sentence Transformer model (default: "all-MiniLM-L6-v2")
                   - cache_ttl: Cache time-to-live in seconds (default: None, no expiry)
        """
        self.config = config or {}
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)
        self.model_name = self.config.get("model_name", "all-MiniLM-L6-v2")
        self.cache_ttl = self.config.get("cache_ttl")
        
        # Initialize Sentence Transformer model
        self._model = None
        self._vector_store = None
    
    def _get_model(self):
        """
        Get or load Sentence Transformer model.
        
        Returns:
            SentenceTransformer model instance
        
        Note:
            Model is loaded lazily on first use.
            This is a pre-trained model, no training needed.
        """
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError as e:
                raise ImportError(
                    f"Failed to load Sentence Transformer model '{self.model_name}'. "
                    f"Install with: pip install sentence-transformers. Error: {e}"
                )
            except Exception as e:
                raise ImportError(
                    f"Failed to load Sentence Transformer model '{self.model_name}'. "
                    f"Error: {e}"
                )
        
        return self._model
    
    def _get_vector_store(self):
        """
        Get or create vector store.
        
        Returns:
            VectorStore instance
        """
        if self._vector_store is None:
            from .vector_store import VectorStore
            self._vector_store = VectorStore(config={
                "similarity_threshold": self.similarity_threshold
            })
        
        return self._vector_store
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Sentence Transformers.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (list of floats)
        
        Example:
            embedding = cache._generate_embedding("Apple reports earnings")
        """
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _get_article_text(self, article: Dict[str, Any]) -> str:
        """
        Extract text from article for embedding.
        
        Combines title and content for better semantic matching.
        
        Args:
            article: News article dictionary
        
        Returns:
            Combined text string
        """
        title = article.get("title", "")
        content = article.get("content", "") or article.get("summary", "")
        
        # Combine title and content (title is more important)
        text = f"{title}. {content}"
        
        # Truncate if too long (models have limits)
        max_length = 500  # Approximate token limit
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def get_similar(self, article: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Check if a similar article exists in cache.
        
        Args:
            article: News article dictionary
            symbol: Stock symbol (for context)
        
        Returns:
            Cached sentiment result if similar article found, None otherwise
        
        Example:
            cached = cache.get_similar(article, "AAPL")
            if cached:
                return cached  # Cache hit!
        """
        vector_store = self._get_vector_store()
        
        # Generate embedding for article
        article_text = self._get_article_text(article)
        embedding = self._generate_embedding(article_text)
        
        # Search for similar articles
        similar_articles = vector_store.search(embedding, top_k=1, threshold=self.similarity_threshold)
        
        if similar_articles:
            # Found similar article - return cached sentiment
            article_id, similarity, metadata = similar_articles[0]
            
            # Extract sentiment from metadata
            if "sentiment_score" in metadata:
                return {
                    "sentiment_score": metadata["sentiment_score"],
                    "sentiment_label": metadata.get("sentiment_label", "neutral"),
                    "confidence": metadata.get("confidence", 0.7),
                    "reasoning": metadata.get("reasoning", "Cached from similar article"),
                    "cached": True,
                    "similarity": float(similarity),
                    "source_article_id": article_id
                }
        
        return None  # Cache miss
    
    def store(self, article: Dict[str, Any], sentiment_result: Dict[str, Any], symbol: str) -> None:
        """
        Store sentiment result in cache.
        
        Args:
            article: News article dictionary
            sentiment_result: Sentiment analysis result from GPT-4
            symbol: Stock symbol
        
        Example:
            cache.store(article, sentiment_result, "AAPL")
        """
        vector_store = self._get_vector_store()
        
        # Generate embedding
        article_text = self._get_article_text(article)
        embedding = self._generate_embedding(article_text)
        
        # Get article ID
        article_id = article.get("id", f"article_{hash(article_text)}")
        
        # Prepare metadata
        metadata = {
            "symbol": symbol,
            "sentiment_score": sentiment_result.get("sentiment_score", 0.0),
            "sentiment_label": sentiment_result.get("sentiment_label", "neutral"),
            "confidence": sentiment_result.get("confidence", 0.7),
            "reasoning": sentiment_result.get("reasoning", ""),
            "title": article.get("title", ""),
            "cached_at": sentiment_result.get("processed_at")
        }
        
        # Store in vector store
        vector_store.add(article_id, embedding, metadata)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats:
            {
                "total_entries": int,
                "similarity_threshold": float,
                "model_name": str
            }
        
        Example:
            stats = cache.get_stats()
        """
        vector_store = self._get_vector_store()
        return {
            "total_entries": vector_store.count(),
            "similarity_threshold": self.similarity_threshold,
            "model_name": self.model_name,
            "cache_ttl": self.cache_ttl
        }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        vector_store = self._get_vector_store()
        vector_store.clear()

