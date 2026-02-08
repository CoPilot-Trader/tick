"""
Alpha Vantage Collector for TICK Data Agent.

Secondary/fallback data source with API key required.
Free tier: 5 API calls per minute, 500 per day.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import requests
import time

from .base import BaseCollector, CollectorResult

logger = logging.getLogger(__name__)


class AlphaVantageCollector(BaseCollector):
    """
    Data collector using Alpha Vantage API.
    
    Supports:
    - Daily, weekly, monthly data (full history)
    - Intraday data: 1min, 5min, 15min, 30min, 60min
    
    Requires API key from: https://www.alphavantage.co/support/#api-key
    
    Rate limits:
    - Free tier: 5 calls/minute, 500 calls/day
    - Premium tiers available
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    # Timeframe to API function mapping
    TIMEFRAME_MAP = {
        "1m": ("TIME_SERIES_INTRADAY", "1min"),
        "5m": ("TIME_SERIES_INTRADAY", "5min"),
        "15m": ("TIME_SERIES_INTRADAY", "15min"),
        "30m": ("TIME_SERIES_INTRADAY", "30min"),
        "1h": ("TIME_SERIES_INTRADAY", "60min"),
        "60m": ("TIME_SERIES_INTRADAY", "60min"),
        "1d": ("TIME_SERIES_DAILY_ADJUSTED", None),
        "daily": ("TIME_SERIES_DAILY_ADJUSTED", None),
        "1wk": ("TIME_SERIES_WEEKLY_ADJUSTED", None),
        "1mo": ("TIME_SERIES_MONTHLY_ADJUSTED", None),
    }
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="alpha_vantage", config=config)
        self.api_key = api_key or (config or {}).get("api_key")
        self._last_call_time = 0
        self._min_interval = 12.5  # 5 calls per minute = 1 call per 12 seconds
        
    def initialize(self) -> bool:
        """Initialize the Alpha Vantage collector."""
        if not self.api_key:
            logger.warning("Alpha Vantage API key not provided")
            self._initialized = False
            return False
        
        self._initialized = True
        logger.info("AlphaVantageCollector initialized")
        return True
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_time = time.time()
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited API request."""
        self._rate_limit()
        
        params["apikey"] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                raise ValueError(data["Error Message"])
            if "Note" in data:  # Rate limit warning
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            
            return data
            
        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")
    
    def fetch_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> CollectorResult:
        """
        Fetch historical OHLCV data from Alpha Vantage.
        
        Args:
            ticker: Stock symbol
            start_date: Start of date range
            end_date: End of date range
            timeframe: Data interval
            
        Returns:
            CollectorResult with normalized DataFrame
        """
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized. API key required."
            )
        
        # Map timeframe
        mapping = self.TIMEFRAME_MAP.get(timeframe)
        if not mapping:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=f"Unsupported timeframe: {timeframe}"
            )
        
        function, interval = mapping
        
        try:
            # Build request parameters
            params = {
                "function": function,
                "symbol": ticker,
                "outputsize": "full",  # Get all available data
            }
            
            if interval:
                params["interval"] = interval
            
            # Make request
            data = self._make_request(params)
            
            # Parse response
            df = self._parse_response(data, function)
            
            if df.empty:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error="No data in response"
                )
            
            # Filter to date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            if df.empty:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No data in range {start_date} to {end_date}"
                )
            
            # Normalize
            normalized_df = self._normalize_dataframe(df, ticker, timeframe)
            
            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else start_date,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else end_date,
                source="alpha_vantage",
                metadata={"function": function, "interval": interval}
            )
            
        except Exception as e:
            logger.error(f"Error fetching {ticker} from Alpha Vantage: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )
    
    def fetch_latest(
        self,
        ticker: str,
        timeframe: str = "5m",
        bars: int = 1
    ) -> CollectorResult:
        """
        Fetch the most recent bars from Alpha Vantage.
        
        Note: Alpha Vantage doesn't have a "latest only" endpoint,
        so we fetch compact data and take the last N bars.
        """
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized"
            )
        
        mapping = self.TIMEFRAME_MAP.get(timeframe)
        if not mapping:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=f"Unsupported timeframe: {timeframe}"
            )
        
        function, interval = mapping
        
        try:
            params = {
                "function": function,
                "symbol": ticker,
                "outputsize": "compact",  # Last 100 data points
            }
            
            if interval:
                params["interval"] = interval
            
            data = self._make_request(params)
            df = self._parse_response(data, function)
            
            if df.empty:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error="No data returned"
                )
            
            # Take last N bars
            df = df.tail(bars)
            normalized_df = self._normalize_dataframe(df, ticker, timeframe)
            
            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else None,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else None,
                source="alpha_vantage",
                metadata={"bars_requested": bars}
            )
            
        except Exception as e:
            logger.error(f"Error fetching latest {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )
    
    def _parse_response(self, data: Dict[str, Any], function: str) -> pd.DataFrame:
        """Parse Alpha Vantage API response into DataFrame."""
        # Find the time series key
        ts_keys = [k for k in data.keys() if "Time Series" in k or "Weekly" in k or "Monthly" in k]
        
        if not ts_keys:
            return pd.DataFrame()
        
        ts_key = ts_keys[0]
        ts_data = data[ts_key]
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(ts_data, orient="index")
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Rename columns (remove numeric prefixes)
        column_map = {}
        for col in df.columns:
            # "1. open" -> "open"
            clean = col.split(". ")[-1].lower()
            column_map[col] = clean
        
        df.rename(columns=column_map, inplace=True)
        
        # Convert to numeric
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        return df
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Alpha Vantage API is operational."""
        if not self.api_key:
            return {
                "status": "unavailable",
                "collector": self.name,
                "error": "No API key configured"
            }
        
        if not self._initialized:
            return {
                "status": "not_initialized",
                "collector": self.name
            }
        
        try:
            # Quick test with IBM (their example ticker)
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "IBM"
            }
            data = self._make_request(params)
            
            if "Global Quote" in data and data["Global Quote"]:
                return {
                    "status": "healthy",
                    "collector": self.name,
                    "test_ticker": "IBM",
                    "last_price": data["Global Quote"].get("05. price")
                }
            
            return {
                "status": "degraded",
                "collector": self.name,
                "warning": "Test query returned unexpected data"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "collector": self.name,
                "error": str(e)
            }




