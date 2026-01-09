"""
Mock News Collector

This module provides a mock news collector for testing and development.
It returns predefined mock news articles without making actual API calls.

Why Mock Collector?
- Test without external API dependencies
- No API keys needed during development
- Predictable test results
- Fast execution (no network calls)
- No API costs

Usage:
    collector = MockNewsCollector()
    articles = collector.fetch_news("AAPL")
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_collector import BaseNewsCollector


class MockNewsCollector(BaseNewsCollector):
    """
    Mock news collector that returns predefined mock data.
    
    This collector loads news articles from a JSON file and returns them
    in the same format as real collectors. This allows testing the entire
    pipeline without external API dependencies.
    
    Example:
        collector = MockNewsCollector()
        articles = collector.fetch_news("AAPL", {"limit": 10})
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock collector.
        
        Args:
            config: Optional configuration:
                   - mock_data_path: Path to mock data JSON file
                                  (default: tests/mocks/news_mock_data.json)
        """
        super().__init__(config)
        self.mock_data_path = self.config.get(
            "mock_data_path",
            Path(__file__).parent.parent / "tests" / "mocks" / "news_mock_data.json"
        )
        self._mock_data = None
    
    def _load_mock_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load mock data from JSON file.
        
        Returns:
            Dictionary mapping ticker symbols to lists of articles
        
        Raises:
            FileNotFoundError: If mock data file doesn't exist
            json.JSONDecodeError: If JSON file is invalid
        """
        if self._mock_data is None:
            if not self.mock_data_path.exists():
                raise FileNotFoundError(f"Mock data file not found: {self.mock_data_path}")
            
            with open(self.mock_data_path, 'r', encoding='utf-8') as f:
                self._mock_data = json.load(f)
        
        return self._mock_data
    
    def fetch_news(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch mock news articles for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")
            params: Optional parameters:
                   - limit: Maximum number of articles (default: all)
        
        Returns:
            List of mock news articles in standard format
        
        Example:
            articles = collector.fetch_news("AAPL", {"limit": 5})
            # Returns first 5 articles for AAPL
        """
        params = params or {}
        limit = params.get("limit")
        
        # Load mock data
        mock_data = self._load_mock_data()
        
        # Get articles for symbol
        articles = mock_data.get(symbol.upper(), [])
        
        # Apply limit if specified
        if limit is not None:
            articles = articles[:limit]
        
        # Add metadata
        for article in articles:
            article["raw_source"] = "mock"
            article["fetched_via"] = "MockNewsCollector"
        
        return articles
    
    def get_source_name(self) -> str:
        """Get the name of the mock source."""
        return "Mock"
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """
        Get mock collector usage information.
        
        Returns:
            Dictionary indicating this is mock data (no API limits).
        """
        return {
            "source": "Mock",
            "is_mock": True,
            "calls_made": 0,
            "calls_remaining": None,
            "rate_limit": "Unlimited (mock data)",
            "reset_time": None,
            "plan": "Mock data - no API calls"
        }

