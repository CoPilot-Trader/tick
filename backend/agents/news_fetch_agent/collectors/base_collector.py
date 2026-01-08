"""
Base News Collector - Abstract Base Class

This module defines the abstract base class for all news collectors.
All news collectors (Finnhub, NewsAPI, Alpha Vantage, Mock) must inherit
from this class and implement the required methods.

Why Abstract Base Class?
- Ensures all collectors have the same interface
- Makes it easy to add new news sources
- Allows polymorphism (use any collector interchangeably)
- Provides type safety and IDE support

Design Pattern: Template Method Pattern
- Defines the structure (what methods are needed)
- Each subclass implements the details (how to fetch from specific API)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseNewsCollector(ABC):
    """
    Abstract base class for all news collectors.
    
    This class defines the interface that all news collectors must implement.
    It ensures consistency across different news sources.
    
    Example:
        class FinnhubCollector(BaseNewsCollector):
            def fetch_news(self, symbol: str, params: dict) -> List[Dict]:
                # Implementation here
                pass
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the news collector.
        
        Args:
            config: Optional configuration dictionary
                   - api_key: API key for the service
                   - timeout: Request timeout in seconds
                   - retry_count: Number of retry attempts
        """
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def fetch_news(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch news articles for a given stock symbol.
        
        This is the main method that all collectors must implement.
        It should fetch news from the specific API and return articles
        in a standardized format.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")
            params: Optional parameters:
                   - date_range: "last_7_days", "last_30_days", etc.
                   - limit: Maximum number of articles to fetch
                   - from_date: Start date (ISO format)
                   - to_date: End date (ISO format)
        
        Returns:
            List of news articles in standardized format:
            [
                {
                    "id": "article_123",
                    "title": "Article Title",
                    "content": "Full article text...",
                    "source": "Reuters",
                    "published_at": "2024-01-15T10:00:00Z",
                    "url": "https://example.com/article",
                    "summary": "Article summary..."
                },
                ...
            ]
        
        Raises:
            NotImplementedError: Must be implemented by subclasses
            ConnectionError: If API connection fails
            ValueError: If symbol is invalid
        """
        raise NotImplementedError(f"{self.name} must implement fetch_news method")
    
    def normalize_response(self, raw_response: Any, symbol: str) -> List[Dict[str, Any]]:
        """
        Normalize API response to standard format.
        
        Different APIs return data in different formats. This method
        converts them to a standard format that the agent expects.
        
        Args:
            raw_response: Raw response from API (format depends on API)
            symbol: Stock symbol (for context)
        
        Returns:
            List of normalized articles in standard format
        
        Note:
            This is a helper method. Subclasses can override it if needed,
            or use the DataNormalizer utility class.
        """
        # Default implementation - subclasses can override
        # For now, return empty list
        return []
    
    def get_source_name(self) -> str:
        """
        Get the name of the news source.
        
        Returns:
            Name of the news source (e.g., "Finnhub", "NewsAPI")
        """
        return self.name
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the collector is healthy and can fetch news.
        
        Returns:
            Dictionary with health status:
            {
                "status": "healthy" or "unhealthy",
                "source": "source_name",
                "message": "Status message"
            }
        """
        return {
            "status": "healthy",
            "source": self.get_source_name(),
            "message": f"{self.name} is operational"
        }
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """
        Get API usage information (calls made, remaining, rate limits).
        
        Returns:
            Dictionary with API usage info:
            {
                "source": "source_name",
                "is_mock": bool,
                "calls_made": int,
                "calls_remaining": Optional[int],
                "rate_limit": Optional[str],
                "reset_time": Optional[str]
            }
        
        Note:
            Subclasses should override this to provide actual API usage data.
            Mock collectors return is_mock=True.
        """
        return {
            "source": self.get_source_name(),
            "is_mock": False,
            "calls_made": 0,
            "calls_remaining": None,
            "rate_limit": None,
            "reset_time": None
        }

