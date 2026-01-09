"""
Data Normalizer

This module provides utilities for normalizing news data from different APIs
into a standard format that the agent expects.

Why Normalization?
- Different APIs return data in different formats
- Finnhub format != NewsAPI format != Alpha Vantage format
- Agent needs consistent format to process articles
- Makes it easy to add new news sources

Standard Format:
{
    "id": "unique_article_id",
    "title": "Article Title",
    "content": "Full article text...",
    "summary": "Article summary...",
    "source": "Source name",
    "published_at": "2024-01-15T10:00:00Z",
    "url": "https://example.com/article"
}
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class DataNormalizer:
    """
    Normalizes news data from different API formats to standard format.
    
    This class converts various API response formats into a consistent
    structure that the agent can process uniformly.
    
    Example:
        normalizer = DataNormalizer()
        standard_article = normalizer.normalize_finnhub(raw_finnhub_data)
        standard_article = normalizer.normalize_newsapi(raw_newsapi_data)
    """
    
    @staticmethod
    def normalize_finnhub(article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Normalize Finnhub API response to standard format.
        
        Finnhub Format:
        {
            "category": "company",
            "datetime": 1705315200,  # Unix timestamp
            "headline": "Article Title",
            "id": 123456,
            "image": "https://...",
            "related": "AAPL",
            "source": "Reuters",
            "summary": "Article summary...",
            "url": "https://..."
        }
        
        Args:
            article: Raw article from Finnhub API
            symbol: Stock symbol (for context)
        
        Returns:
            Normalized article in standard format
        
        Example:
            normalized = DataNormalizer.normalize_finnhub(finnhub_article, "AAPL")
        """
        # TODO: Implement Finnhub normalization
        # 1. Extract fields from Finnhub format
        # 2. Convert Unix timestamp to ISO format
        # 3. Map fields to standard format
        # 4. Handle missing fields gracefully
        # 5. Return normalized article
        
        # Placeholder implementation
        return {
            "id": str(article.get("id", "")),
            "title": article.get("headline", ""),
            "content": article.get("summary", ""),
            "summary": article.get("summary", ""),
            "source": article.get("source", "Unknown"),
            "published_at": DataNormalizer._timestamp_to_iso(article.get("datetime")),
            "url": article.get("url", ""),
            "raw_source": "finnhub"
        }
    
    @staticmethod
    def normalize_newsapi(article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Normalize NewsAPI response to standard format.
        
        NewsAPI Format:
        {
            "source": {"id": "reuters", "name": "Reuters"},
            "author": "John Doe",
            "title": "Article Title",
            "description": "Article description...",
            "url": "https://...",
            "publishedAt": "2024-01-15T10:00:00Z",
            "content": "Full article content..."
        }
        
        Args:
            article: Raw article from NewsAPI
            symbol: Stock symbol (for context)
        
        Returns:
            Normalized article in standard format
        
        Example:
            normalized = DataNormalizer.normalize_newsapi(newsapi_article, "AAPL")
        """
        # TODO: Implement NewsAPI normalization
        # 1. Extract fields from NewsAPI format
        # 2. Handle nested source object
        # 3. Map fields to standard format
        # 4. Handle missing fields gracefully
        # 5. Return normalized article
        
        # Placeholder implementation
        source_obj = article.get("source", {})
        source_name = source_obj.get("name", "Unknown") if isinstance(source_obj, dict) else "Unknown"
        
        return {
            "id": article.get("url", ""),  # Use URL as ID if no ID provided
            "title": article.get("title", ""),
            "content": article.get("content", "") or article.get("description", ""),
            "summary": article.get("description", ""),
            "source": source_name,
            "published_at": article.get("publishedAt", ""),
            "url": article.get("url", ""),
            "raw_source": "newsapi"
        }
    
    @staticmethod
    def normalize_alpha_vantage(article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Normalize Alpha Vantage API response to standard format.
        
        Args:
            article: Raw article from Alpha Vantage API
            symbol: Stock symbol (for context)
        
        Returns:
            Normalized article in standard format
        """
        # TODO: Implement Alpha Vantage normalization
        # 1. Extract fields from Alpha Vantage format
        # 2. Map fields to standard format
        # 3. Handle missing fields gracefully
        # 4. Return normalized article
        
        # Placeholder implementation
        return {
            "id": article.get("url", ""),
            "title": article.get("title", ""),
            "content": article.get("text", ""),
            "summary": article.get("summary", ""),
            "source": article.get("source", "Unknown"),
            "published_at": article.get("time_published", ""),
            "url": article.get("url", ""),
            "raw_source": "alpha_vantage"
        }
    
    @staticmethod
    def _timestamp_to_iso(timestamp: Optional[int]) -> str:
        """
        Convert Unix timestamp to ISO format string.
        
        Args:
            timestamp: Unix timestamp (seconds since epoch)
        
        Returns:
            ISO format string (e.g., "2024-01-15T10:00:00Z")
        """
        if timestamp is None:
            return datetime.utcnow().isoformat() + "Z"
        
        try:
            dt = datetime.utcfromtimestamp(timestamp)
            return dt.isoformat() + "Z"
        except (ValueError, OSError):
            return datetime.utcnow().isoformat() + "Z"
    
    @staticmethod
    def normalize_batch(articles: List[Dict[str, Any]], source: str, symbol: str) -> List[Dict[str, Any]]:
        """
        Normalize a batch of articles from a specific source.
        
        Args:
            articles: List of raw articles
            source: Source name ("finnhub", "newsapi", "alpha_vantage")
            symbol: Stock symbol
        
        Returns:
            List of normalized articles
        
        Example:
            normalized = DataNormalizer.normalize_batch(articles, "finnhub", "AAPL")
        """
        normalizer_map = {
            "finnhub": DataNormalizer.normalize_finnhub,
            "newsapi": DataNormalizer.normalize_newsapi,
            "alpha_vantage": DataNormalizer.normalize_alpha_vantage,
        }
        
        normalizer = normalizer_map.get(source.lower())
        if not normalizer:
            raise ValueError(f"Unknown source: {source}")
        
        return [normalizer(article, symbol) for article in articles]

