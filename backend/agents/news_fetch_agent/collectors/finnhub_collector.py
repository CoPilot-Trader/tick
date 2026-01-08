"""
Finnhub News Collector

This module provides integration with Finnhub API for fetching financial news.

Finnhub API:
- Provides company news, general news, and market news
- Free tier: 60 API calls/minute
- Requires API key

API Documentation: https://finnhub.io/docs/api/company-news

Why Finnhub?
- Reliable financial news source
- Good coverage of major stocks
- Free tier available
- Real-time and historical news
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .base_collector import BaseNewsCollector
from ..utils import DataNormalizer, get_logger, retry_with_backoff

logger = get_logger(__name__)


class FinnhubCollector(BaseNewsCollector):
    """
    Collector for fetching news from Finnhub API.
    
    This collector makes HTTP requests to Finnhub API and returns
    news articles in standardized format.
    
    Example:
        collector = FinnhubCollector(config={"api_key": "your_key"})
        articles = collector.fetch_news("AAPL")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Finnhub collector.
        
        Args:
            config: Configuration dictionary:
                   - api_key: Finnhub API key (required)
                   - base_url: API base URL (default: https://finnhub.io/api/v1)
                   - timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("Finnhub API key is required in config")
        
        self.base_url = self.config.get("base_url", "https://finnhub.io/api/v1")
        self.timeout = self.config.get("timeout", 30)
        
        # API usage tracking
        self._calls_made = 0
        self._rate_limit_per_minute = 60  # Free tier: 60 calls/minute
        self._last_call_time = None
        self._last_reset_time = None  # Track when counter was last reset
        self._rate_limit_remaining_from_header = None  # From API headers (for reference only)
    
    def fetch_news(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch news from Finnhub API for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            params: Optional parameters:
                   - from_date: Start date (datetime object or YYYY-MM-DD string)
                   - to_date: End date (datetime object or YYYY-MM-DD string)
                   - limit: Maximum number of articles
        
        Returns:
            List of news articles in standardized format
        
        Raises:
            ConnectionError: If API request fails
            ValueError: If symbol is invalid
            KeyError: If API key is invalid
        
        API Endpoint:
            GET https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from}&to={to}&token={token}
        """
        params = params or {}
        symbol = symbol.upper()
        
        # Extract and format dates
        from_date = params.get("from_date")
        to_date = params.get("to_date")
        limit = params.get("limit")
        
        # Format dates for Finnhub API (YYYY-MM-DD)
        if from_date:
            if isinstance(from_date, datetime):
                from_date_str = from_date.strftime("%Y-%m-%d")
            else:
                from_date_str = str(from_date)[:10]  # Take first 10 chars (YYYY-MM-DD)
        else:
            # Default to 7 days ago if not provided
            from_date_str = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).strftime("%Y-%m-%d")
        
        if to_date:
            if isinstance(to_date, datetime):
                to_date_str = to_date.strftime("%Y-%m-%d")
            else:
                to_date_str = str(to_date)[:10]
        else:
            # Default to today
            to_date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Build API URL
        url = f"{self.base_url}/company-news"
        query_params = {
            "symbol": symbol,
            "from": from_date_str,
            "to": to_date_str,
            "token": self.api_key
        }
        
        try:
            # Track API call and reset logic
            now = datetime.now(timezone.utc)
            
            # Reset counter if 1 minute has passed since last reset
            if self._last_reset_time is None:
                self._last_reset_time = now
            elif (now - self._last_reset_time).total_seconds() >= 60:
                self._calls_made = 0
                self._last_reset_time = now
            
            self._calls_made += 1
            self._last_call_time = now
            
            # Make HTTP GET request with retry logic
            logger.debug(f"Fetching news from Finnhub for {symbol} (from {from_date_str} to {to_date_str})")
            response = self._make_request_with_retry(url, query_params)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Check rate limit headers if available (for reference only, we use local tracking)
            rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
            if rate_limit_remaining:
                try:
                    # Store header value for reference, but don't use it for primary tracking
                    self._rate_limit_remaining_from_header = int(rate_limit_remaining)
                except:
                    pass
            
            # Parse JSON response
            data = response.json()
            
            # Finnhub returns a list of articles directly
            if not isinstance(data, list):
                return []
            
            # Normalize articles to standard format
            normalized_articles = []
            for article in data:
                try:
                    normalized = DataNormalizer.normalize_finnhub(article, symbol)
                    if normalized:
                        normalized_articles.append(normalized)
                except Exception as e:
                    logger.warning(f"Error normalizing Finnhub article: {e}")
                    continue
            
            # Apply limit if specified
            if limit and limit > 0:
                normalized_articles = normalized_articles[:limit]
            
            return normalized_articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub API request failed: {str(e)}")
            raise ConnectionError(f"Finnhub API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid response from Finnhub API: {str(e)}")
            raise ValueError(f"Invalid response from Finnhub API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching news from Finnhub: {str(e)}", exc_info=True)
            raise Exception(f"Unexpected error fetching news from Finnhub: {str(e)}")
    
    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=60.0,
        exceptions=(requests.exceptions.RequestException, requests.exceptions.Timeout, ConnectionError)
    )
    def _make_request_with_retry(self, url: str, params: Dict[str, Any]) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: API endpoint URL
            params: Query parameters
        
        Returns:
            HTTP response object
        
        Raises:
            requests.exceptions.RequestException: If request fails after retries
        """
        return requests.get(url, params=params, timeout=self.timeout)
    
    def get_source_name(self) -> str:
        """Get the name of the source."""
        return "Finnhub"
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """
        Get Finnhub API usage information.
        
        Returns:
            Dictionary with API usage info including rate limits.
        """
        # Reset counter if 1 minute has passed since last reset
        now = datetime.now(timezone.utc)
        if self._last_reset_time is None:
            self._last_reset_time = now
        elif (now - self._last_reset_time).total_seconds() >= 60:
            self._calls_made = 0
            self._last_reset_time = now
        
        # Always use local tracking (more accurate than API headers)
        # Calculate: 60 calls per minute, reset every minute
        calls_remaining = max(0, self._rate_limit_per_minute - self._calls_made)
        
        # Calculate next reset time
        if self._last_reset_time:
            next_reset = self._last_reset_time.replace(second=0, microsecond=0)
            if next_reset <= now:
                next_reset = next_reset.replace(minute=next_reset.minute + 1)
            reset_time_str = next_reset.isoformat()
        else:
            reset_time_str = "N/A"
        
        return {
            "source": "Finnhub",
            "is_mock": False,
            "calls_made": self._calls_made,
            "calls_remaining": calls_remaining,
            "rate_limit": f"{self._rate_limit_per_minute} calls/minute",
            "reset_time": reset_time_str,
            "plan": "Free tier (estimated)"
        }

