"""
yfinance Collector for TICK Data Agent.

Primary data source for historical and real-time OHLCV data.
Free tier with reasonable rate limits.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from .base import BaseCollector, CollectorResult

logger = logging.getLogger(__name__)


class YFinanceCollector(BaseCollector):
    """
    Data collector using yfinance library.
    
    Supports:
    - Historical data up to several years
    - Intraday data (limited by Yahoo Finance API)
    - Multiple timeframes: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
    
    Limitations:
    - Intraday data only available for last 60 days (5m, 15m, 30m, 1h)
    - 1-minute data only for last 7 days
    """
    
    # Timeframe mapping to yfinance intervals
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m", 
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "60m": "1h",  # Alias
        "4h": "4h",
        "1d": "1d",
        "daily": "1d",  # Alias
        "1wk": "1wk",
        "1mo": "1mo",
    }
    
    # Maximum history for each timeframe
    HISTORY_LIMITS = {
        "1m": timedelta(days=7),
        "5m": timedelta(days=60),
        "15m": timedelta(days=60),
        "30m": timedelta(days=60),
        "1h": timedelta(days=730),
        "4h": timedelta(days=730),
        "1d": timedelta(days=365 * 10),
        "1wk": timedelta(days=365 * 10),
        "1mo": timedelta(days=365 * 10),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="yfinance", config=config)
        
    def initialize(self) -> bool:
        """Initialize the yfinance collector."""
        if not YFINANCE_AVAILABLE:
            logger.error("yfinance package not installed")
            self._initialized = False
            return False
        
        self._initialized = True
        logger.info("YFinanceCollector initialized")
        return True
    
    def fetch_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> CollectorResult:
        """
        Fetch historical OHLCV data from Yahoo Finance.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL", "SPY")
            start_date: Start of date range
            end_date: End of date range
            timeframe: Data interval ("5m", "1h", "1d", etc.)
            
        Returns:
            CollectorResult with normalized DataFrame
        """
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized"
            )
        
        # Map timeframe to yfinance interval
        yf_interval = self.TIMEFRAME_MAP.get(timeframe)
        if not yf_interval:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=f"Unsupported timeframe: {timeframe}"
            )
        
        # Check history limits for intraday
        max_history = self.HISTORY_LIMITS.get(yf_interval, timedelta(days=365 * 10))
        min_start = datetime.now() - max_history
        if start_date < min_start:
            logger.warning(
                f"Adjusting start_date for {ticker} ({timeframe}): "
                f"{start_date} -> {min_start}"
            )
            start_date = min_start
        
        try:
            # Create ticker object
            stock = yf.Ticker(ticker)

            # For intraday timeframes, use period-based fetch to handle
            # weekends/holidays (explicit date ranges return empty on non-trading days)
            is_intraday = yf_interval in ("1m", "5m", "15m", "30m", "1h", "4h")
            requested_days = max(1, (end_date - start_date).days)

            if is_intraday and requested_days <= 5:
                # Use period='5d' which auto-returns most recent trading day(s)
                df = stock.history(
                    period=f"{min(requested_days + 2, 60)}d",
                    interval=yf_interval,
                    auto_adjust=True,
                    prepost=False,
                )
            else:
                df = stock.history(
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    interval=yf_interval,
                    auto_adjust=True,
                    prepost=False,
                )

            if df.empty:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No data returned for {ticker}"
                )
            
            # Normalize to standard format
            normalized_df = self._normalize_dataframe(df, ticker, timeframe)
            
            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else start_date,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else end_date,
                source="yfinance",
                metadata={
                    "adjusted": True,
                    "interval": yf_interval,
                }
            )
            
        except Exception as e:
            logger.error(f"Error fetching {ticker} from yfinance: {e}")
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
        Fetch the most recent bars.
        
        Args:
            ticker: Stock symbol
            timeframe: Data interval
            bars: Number of recent bars to fetch
            
        Returns:
            CollectorResult with latest data
        """
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized"
            )
        
        yf_interval = self.TIMEFRAME_MAP.get(timeframe)
        if not yf_interval:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=f"Unsupported timeframe: {timeframe}"
            )
        
        try:
            stock = yf.Ticker(ticker)
            
            # Determine period based on bars needed
            if timeframe in ["1m", "5m", "15m", "30m"]:
                period = "1d" if bars <= 78 else "5d"  # ~78 5-min bars per day
            elif timeframe == "1h":
                period = "5d" if bars <= 35 else "1mo"
            else:
                period = "1mo" if bars <= 22 else "3mo"
            
            df = stock.history(
                period=period,
                interval=yf_interval,
                auto_adjust=True,
                prepost=False,
            )
            
            if df.empty:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No recent data for {ticker}"
                )
            
            # Take only the requested number of bars
            df = df.tail(bars)
            
            # Normalize
            normalized_df = self._normalize_dataframe(df, ticker, timeframe)
            
            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else None,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else None,
                source="yfinance",
                metadata={"period": period, "bars_requested": bars}
            )
            
        except Exception as e:
            logger.error(f"Error fetching latest {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )
    
    def fetch_info(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch ticker info (company name, sector, etc.).
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Dictionary with ticker information
        """
        if not self._initialized or not YFINANCE_AVAILABLE:
            return {"error": "Collector not available"}
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "symbol": ticker,
                "name": info.get("shortName", info.get("longName", ticker)),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
                "exchange": info.get("exchange"),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if yfinance is operational."""
        if not YFINANCE_AVAILABLE:
            return {
                "status": "unavailable",
                "collector": self.name,
                "error": "yfinance package not installed"
            }
        
        if not self._initialized:
            return {
                "status": "not_initialized",
                "collector": self.name
            }
        
        # Quick test with multiple tickers (Yahoo Finance can be flaky)
        test_tickers = ["AAPL", "MSFT", "SPY"]
        
        for ticker in test_tickers:
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period="5d")  # Try 5 days for more reliability
                
                if not df.empty:
                    return {
                        "status": "healthy",
                        "collector": self.name,
                        "test_ticker": ticker,
                        "last_bar": df.index[-1].isoformat() if len(df) > 0 else None
                    }
            except Exception as e:
                logger.debug(f"Health check failed for {ticker}: {e}")
                continue
        
        # If all tickers failed, report degraded but still operational
        return {
            "status": "degraded",
            "collector": self.name,
            "warning": "Yahoo Finance API may be experiencing issues. Will retry on actual requests."
        }

