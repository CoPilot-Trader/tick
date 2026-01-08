"""
News Collectors Package

This package contains all news collection modules for fetching news from
various sources (Finnhub, NewsAPI, Alpha Vantage, and Mock data for testing).

Why this package exists:
- Separates news collection logic from main agent
- Makes it easy to add new news sources
- Allows testing with mock data
- Ensures consistent interface across all collectors
"""

from .base_collector import BaseNewsCollector
from .mock_collector import MockNewsCollector
from .finnhub_collector import FinnhubCollector
from .newsapi_collector import NewsAPICollector
from .alpha_vantage_collector import AlphaVantageCollector
from .alpha_vantage_collector import AlphaVantageCollector

__all__ = [
    "BaseNewsCollector",
    "MockNewsCollector",
    "FinnhubCollector",
    "NewsAPICollector",
    "AlphaVantageCollector",
    "AlphaVantageCollector",
]

