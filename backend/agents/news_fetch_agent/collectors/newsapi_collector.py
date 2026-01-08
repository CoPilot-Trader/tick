"""
NewsAPI News Collector

This module provides integration with NewsAPI for fetching financial news.

NewsAPI:
- Aggregates news from multiple sources
- Free tier: 1,000 requests/day
- Requires API key
- Good for general news search

API Documentation: https://newsapi.org/docs

Why NewsAPI?
- Aggregates multiple news sources
- Good search capabilities
- Free tier available
- Covers major news outlets
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from .base_collector import BaseNewsCollector
from ..utils import DataNormalizer, SectorMapper, get_logger, retry_with_backoff

logger = get_logger(__name__)


class NewsAPICollector(BaseNewsCollector):
    """
    Collector for fetching news from NewsAPI.
    
    This collector makes HTTP requests to NewsAPI and returns
    news articles in standardized format.
    
    Example:
        collector = NewsAPICollector(config={"api_key": "your_key"})
        articles = collector.fetch_news("AAPL")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NewsAPI collector.
        
        Args:
            config: Configuration dictionary:
                   - api_key: NewsAPI key (required)
                   - base_url: API base URL (default: https://newsapi.org/v2)
                   - timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("NewsAPI key is required in config")
        
        self.base_url = self.config.get("base_url", "https://newsapi.org/v2")
        self.timeout = self.config.get("timeout", 30)
        
        # API usage tracking
        self._calls_made = 0
        self._rate_limit_per_day = 1000  # Free tier: 1,000 requests/day
        self._last_call_time = None
        self._last_reset_date = None  # Track when counter was last reset (date only)
        self._rate_limit_remaining_from_header = None  # From API headers (for reference only)
    
    def fetch_news(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch news from NewsAPI for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            params: Optional parameters:
                   - from_date: Start date (datetime object or ISO string)
                   - to_date: End date (datetime object or ISO string)
                   - limit: Maximum number of articles
                   - language: Language code (default: "en")
        
        Returns:
            List of news articles in standardized format
        
        Raises:
            ConnectionError: If API request fails
            ValueError: If symbol is invalid
            KeyError: If API key is invalid
        
        API Endpoint:
            GET https://newsapi.org/v2/everything?q={query}&from={from}&to={to}
        """
        params = params or {}
        symbol = symbol.upper()
        
        # Extract dates
        from_date = params.get("from_date")
        to_date = params.get("to_date")
        limit = params.get("limit", 100)  # NewsAPI default is 100
        language = params.get("language", "en")
        
        # Format dates for NewsAPI (YYYY-MM-DD or ISO format)
        if from_date:
            if isinstance(from_date, datetime):
                from_date_str = from_date.strftime("%Y-%m-%d")
            else:
                from_date_str = str(from_date)[:10]  # Take first 10 chars
        else:
            # Default to 7 days ago
            from_date_str = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).strftime("%Y-%m-%d")
        
        if to_date:
            if isinstance(to_date, datetime):
                to_date_str = to_date.strftime("%Y-%m-%d")
            else:
                to_date_str = str(to_date)[:10]
        else:
            # Default to today
            to_date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Build search query (symbol + company name if available)
        query = symbol
        try:
            sector_mapper = SectorMapper()
            company_names = sector_mapper.COMPANY_NAMES.get(symbol, [])
            if company_names:
                # Add first company name to query
                query = f"{symbol} OR {company_names[0]}"
        except:
            pass  # If sector mapper fails, just use symbol
        
        # Build API URL
        url = f"{self.base_url}/everything"
        query_params = {
            "q": query,
            "from": from_date_str,
            "to": to_date_str,
            "language": language,
            "sortBy": "publishedAt",  # Sort by publication date
            "pageSize": min(limit, 100)  # NewsAPI max is 100 per request
        }
        
        # NewsAPI requires API key in header
        headers = {
            "X-Api-Key": self.api_key
        }
        
        try:
            # Track API call and reset logic
            now = datetime.now(timezone.utc)
            today = now.date()
            
            # Reset counter if new day
            if self._last_reset_date is None:
                self._last_reset_date = today
            elif self._last_reset_date != today:
                self._calls_made = 0
                self._last_reset_date = today
                self._rate_limit_remaining = None  # Clear cached header value
            
            self._calls_made += 1
            self._last_call_time = now
            
            # Make HTTP GET request with retry logic
            logger.debug(f"Fetching news from NewsAPI for {symbol} (from {from_date_str} to {to_date_str})")
            response = self._make_request_with_retry(url, query_params, headers)
            response.raise_for_status()
            
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
            
            # NewsAPI returns {"status": "ok", "articles": [...]}
            if data.get("status") != "ok":
                error_message = data.get("message", "Unknown error")
                raise ValueError(f"NewsAPI returned error: {error_message}")
            
            articles = data.get("articles", [])
            if not articles:
                return []
            
            # Normalize articles to standard format
            normalized_articles = []
            for article in articles:
                try:
                    normalized = DataNormalizer.normalize_newsapi(article, symbol)
                    if normalized:
                        normalized_articles.append(normalized)
                except Exception as e:
                    logger.warning(f"Error normalizing NewsAPI article: {e}")
                    continue
            
            # Apply limit if specified
            if limit and limit > 0:
                normalized_articles = normalized_articles[:limit]
            
            return normalized_articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"NewsAPI request failed: {str(e)}")
            raise ConnectionError(f"NewsAPI request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid response from NewsAPI: {str(e)}")
            raise ValueError(f"Invalid response from NewsAPI: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching news from NewsAPI: {str(e)}", exc_info=True)
            raise Exception(f"Unexpected error fetching news from NewsAPI: {str(e)}")
    
    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=60.0,
        exceptions=(requests.exceptions.RequestException, requests.exceptions.Timeout, ConnectionError)
    )
    def _make_request_with_retry(self, url: str, params: Dict[str, Any], headers: Dict[str, str]) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            headers: HTTP headers
        
        Returns:
            HTTP response object
        
        Raises:
            requests.exceptions.RequestException: If request fails after retries
        """
        return requests.get(url, params=params, headers=headers, timeout=self.timeout)
    
    def get_source_name(self) -> str:
        """Get the name of the source."""
        return "NewsAPI"
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """
        Get NewsAPI usage information.
        
        Returns:
            Dictionary with API usage info including rate limits.
        """
        # Reset counter if new day
        now = datetime.now(timezone.utc)
        today = now.date()
        if self._last_reset_date is None:
            self._last_reset_date = today
        elif self._last_reset_date != today:
            self._calls_made = 0
            self._last_reset_date = today
        
        # Always use local tracking (more accurate than API headers)
        # Calculate: 1,000 calls per day, reset daily
        calls_remaining = max(0, self._rate_limit_per_day - self._calls_made)
        
        # Calculate next reset time (midnight UTC of next day)
        if self._last_reset_date:
            next_reset = datetime.combine(
                self._last_reset_date + timedelta(days=1),
                datetime.min.time(),
                tzinfo=timezone.utc
            )
            reset_time_str = next_reset.isoformat()
        else:
            reset_time_str = "N/A"
        
        return {
            "source": "NewsAPI",
            "is_mock": False,
            "calls_made": self._calls_made,
            "calls_remaining": calls_remaining,
            "rate_limit": f"{self._rate_limit_per_day} calls/day",
            "reset_time": reset_time_str,
            "plan": "Free tier (estimated)"
        }

