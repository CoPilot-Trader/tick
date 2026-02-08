"""
Base Collector interface for TICK Data Agent.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd


@dataclass
class CollectorResult:
    """Result from a data collection operation."""
    
    success: bool
    ticker: str
    timeframe: str
    data: Optional[pd.DataFrame] = None
    rows_fetched: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "ticker": self.ticker,
            "timeframe": self.timeframe,
            "rows_fetched": self.rows_fetched,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "source": self.source,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseCollector(ABC):
    """
    Abstract base class for data collectors.
    
    All collectors must implement:
    - fetch_historical(): For batch historical data
    - fetch_latest(): For real-time/recent data
    - health_check(): To verify API connectivity
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the collector (API keys, connections, etc.)."""
        pass
    
    @abstractmethod
    def fetch_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> CollectorResult:
        """
        Fetch historical OHLCV data.
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            start_date: Start of date range
            end_date: End of date range
            timeframe: Data interval ("5m", "1h", "1d")
            
        Returns:
            CollectorResult with DataFrame or error
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check if the collector is operational."""
        pass
    
    def _normalize_dataframe(self, df: pd.DataFrame, ticker: str, timeframe: str) -> pd.DataFrame:
        """
        Normalize DataFrame to standard TICK format.
        
        Standard columns: [ticker, timeframe, bar_ts, open, high, low, close, volume]
        
        Reference: Client's DATA_LAKE_SCHEMA_STANDARD.md
        """
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "ticker", "timeframe", "bar_ts", "open", "high", "low", "close", "volume"
            ])
        
        # Copy to avoid modifying original
        result = df.copy()
        
        # Ensure lowercase column names
        result.columns = result.columns.str.lower()
        
        # Rename common variations
        column_map = {
            "datetime": "bar_ts",
            "date": "bar_ts",
            "timestamp": "bar_ts",
            "time": "bar_ts",
            "adj close": "adj_close",
            "adj_close": "adj_close",
        }
        result.rename(columns=column_map, inplace=True)
        
        # Handle index as timestamp
        if result.index.name in ["datetime", "date", "Date", "Datetime"]:
            result["bar_ts"] = result.index
            result.reset_index(drop=True, inplace=True)
        elif "bar_ts" not in result.columns and isinstance(result.index, pd.DatetimeIndex):
            result["bar_ts"] = result.index
            result.reset_index(drop=True, inplace=True)
        
        # Ensure bar_ts is datetime
        if "bar_ts" in result.columns:
            result["bar_ts"] = pd.to_datetime(result["bar_ts"])
        
        # Add metadata columns
        result["ticker"] = ticker.upper()
        result["timeframe"] = timeframe
        
        # Select and order standard columns
        standard_cols = ["ticker", "timeframe", "bar_ts", "open", "high", "low", "close", "volume"]
        available_cols = [c for c in standard_cols if c in result.columns]
        
        return result[available_cols]
    
    def _validate_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe string."""
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"]
        return timeframe in valid_timeframes
    
    @property
    def is_initialized(self) -> bool:
        """Check if collector is initialized."""
        return self._initialized




