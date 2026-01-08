"""
Alpha Vantage News Collector

This module provides integration with Alpha Vantage API for fetching financial news.

Alpha Vantage API:
- Provides company news and market news
- Free tier: 5 API calls/minute, 500 calls/day
- Requires API key
- Good as fallback option

API Documentation: https://www.alphavantage.co/documentation/

Why Alpha Vantage?
- Free tier available
- Good as backup/fallback source
- Reliable service
- Covers major stocks
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_collector import BaseNewsCollector
from ..utils import DataNormalizer, get_logger, retry_with_backoff

logger = get_logger(__name__)


class AlphaVantageCollector(BaseNewsCollector):
    """
    Collector for fetching news from Alpha Vantage API.
    
    This collector makes HTTP requests to Alpha Vantage API and returns
    news articles in standardized format. Used as a fallback option
    when primary sources fail.
    
    Example:
        collector = AlphaVantageCollector(config={"api_key": "your_key"})
        articles = collector.fetch_news("AAPL")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Alpha Vantage collector.
        
        Args:
            config: Configuration dictionary:
                   - api_key: Alpha Vantage API key (required)
                   - base_url: API base URL (default: https://www.alphavantage.co/query)
                   - timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required in config")
        
        self.base_url = self.config.get("base_url", "https://www.alphavantage.co/query")
        self.timeout = self.config.get("timeout", 30)
        
        # API usage tracking
        self._calls_made_minute = 0  # Track calls per minute
        self._calls_made_day = 0     # Track calls per day
        self._rate_limit_per_minute = 5  # Free tier: 5 calls/minute
        self._rate_limit_per_day = 500   # Free tier: 500 calls/day
        self._last_call_time = None
        self._last_minute_reset = None  # Track when minute counter was last reset
        self._last_day_reset = None     # Track when day counter was last reset
    
    def fetch_news(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch news from Alpha Vantage API for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            params: Optional parameters:
                   - limit: Maximum number of articles
                   - from_date: Start date (not directly supported, but used for filtering)
                   - to_date: End date (not directly supported, but used for filtering)
        
        Returns:
            List of news articles in standardized format
        
        Raises:
            ConnectionError: If API request fails
            ValueError: If symbol is invalid
            KeyError: If API key is invalid
        
        API Endpoint:
            GET https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={key}
        
        Note:
            Alpha Vantage NEWS_SENTIMENT endpoint doesn't support date filtering directly.
            We'll fetch recent news and filter by date in post-processing.
        """
        params = params or {}
        symbol = symbol.upper()
        limit = params.get("limit", 50)
        
        # Build API URL
        url = self.base_url
        query_params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "apikey": self.api_key,
            "limit": min(limit, 1000)  # Alpha Vantage max is 1000
        }
        
        try:
            # Track API call and reset logic
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            today = now.date()
            
            # Reset minute counter if 1 minute has passed
            if self._last_minute_reset is None:
                self._last_minute_reset = now
            elif (now - self._last_minute_reset).total_seconds() >= 60:
                self._calls_made_minute = 0
                self._last_minute_reset = now
            
            # Reset day counter if new day
            if self._last_day_reset is None:
                self._last_day_reset = today
            elif self._last_day_reset != today:
                self._calls_made_day = 0
                self._last_day_reset = today
            
            self._calls_made_minute += 1
            self._calls_made_day += 1
            self._last_call_time = now
            
            # Make HTTP GET request with retry logic
            logger.debug(f"Fetching news from Alpha Vantage for {symbol}")
            response = self._make_request_with_retry(url, query_params)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            if "Note" in data:
                # Rate limit message
                raise ConnectionError(f"Alpha Vantage rate limit: {data['Note']}")
            
            # Alpha Vantage returns {"feed": [...]}
            articles = data.get("feed", [])
            if not articles:
                return []
            
            # Extract date range for filtering (if provided)
            from_date = params.get("from_date")
            to_date = params.get("to_date")
            
            # Normalize articles to standard format and filter by date
            normalized_articles = []
            for article in articles:
                try:
                    normalized = DataNormalizer.normalize_alpha_vantage(article, symbol)
                    if not normalized:
                        continue
                    
                    # Filter by date if date range provided
                    if from_date or to_date:
                        published_at_str = normalized.get("published_at", "")
                        if published_at_str:
                            try:
                                # Parse published_at
                                if isinstance(published_at_str, str):
                                    if published_at_str.endswith('Z'):
                                        published_at_str = published_at_str[:-1] + '+00:00'
                                    article_time = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                                    if article_time.tzinfo is None:
                                        from datetime import timezone
                                        article_time = article_time.replace(tzinfo=timezone.utc)
                                    
                                    # Check if within date range
                                    if from_date:
                                        if isinstance(from_date, str):
                                            from_date_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                                        else:
                                            from_date_dt = from_date
                                        if from_date_dt.tzinfo is None:
                                            from datetime import timezone
                                            from_date_dt = from_date_dt.replace(tzinfo=timezone.utc)
                                        if article_time < from_date_dt:
                                            continue
                                    
                                    if to_date:
                                        if isinstance(to_date, str):
                                            to_date_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                                        else:
                                            to_date_dt = to_date
                                        if to_date_dt.tzinfo is None:
                                            from datetime import timezone
                                            to_date_dt = to_date_dt.replace(tzinfo=timezone.utc)
                                        if article_time > to_date_dt:
                                            continue
                            except Exception:
                                # If date parsing fails, include the article anyway
                                pass
                    
                    normalized_articles.append(normalized)
                except Exception as e:
                    logger.warning(f"Error normalizing Alpha Vantage article: {e}")
                    continue
            
            # Apply limit if specified
            if limit and limit > 0:
                normalized_articles = normalized_articles[:limit]
            
            return normalized_articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpha Vantage API request failed: {str(e)}")
            raise ConnectionError(f"Alpha Vantage API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid response from Alpha Vantage API: {str(e)}")
            raise ValueError(f"Invalid response from Alpha Vantage API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching news from Alpha Vantage: {str(e)}", exc_info=True)
            raise Exception(f"Unexpected error fetching news from Alpha Vantage: {str(e)}")
    
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
        return "Alpha Vantage"
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """
        Get Alpha Vantage API usage information.
        
        Returns:
            Dictionary with API usage info including rate limits.
        """
        from datetime import datetime, timezone, timedelta
        
        # Reset counters if time windows have passed
        now = datetime.now(timezone.utc)
        today = now.date()
        
        # Reset minute counter if 1 minute has passed
        if self._last_minute_reset is None:
            self._last_minute_reset = now
        elif (now - self._last_minute_reset).total_seconds() >= 60:
            self._calls_made_minute = 0
            self._last_minute_reset = now
        
        # Reset day counter if new day
        if self._last_day_reset is None:
            self._last_day_reset = today
        elif self._last_day_reset != today:
            self._calls_made_day = 0
            self._last_day_reset = today
        
        # Calculate remaining calls for both limits
        calls_remaining_minute = max(0, self._rate_limit_per_minute - self._calls_made_minute)
        calls_remaining_day = max(0, self._rate_limit_per_day - self._calls_made_day)
        
        # Use the stricter limit (whichever is lower)
        calls_remaining = min(calls_remaining_minute, calls_remaining_day)
        
        # Calculate next reset times
        if self._last_minute_reset:
            next_minute_reset = self._last_minute_reset.replace(second=0, microsecond=0)
            if next_minute_reset <= now:
                next_minute_reset = next_minute_reset.replace(minute=next_minute_reset.minute + 1)
            minute_reset_str = next_minute_reset.isoformat()
        else:
            minute_reset_str = "N/A"
        
        if self._last_day_reset:
            next_day_reset = datetime.combine(
                self._last_day_reset + timedelta(days=1),
                datetime.min.time(),
                tzinfo=timezone.utc
            )
            day_reset_str = next_day_reset.isoformat()
        else:
            day_reset_str = "N/A"
        
        return {
            "source": "Alpha Vantage",
            "is_mock": False,
            "calls_made": self._calls_made_day,  # Report daily calls as primary metric
            "calls_remaining": calls_remaining,
            "rate_limit": f"{self._rate_limit_per_minute} calls/minute, {self._rate_limit_per_day} calls/day",
            "reset_time_minute": minute_reset_str,
            "reset_time_day": day_reset_str,
            "plan": "Free tier (estimated)"
        }

