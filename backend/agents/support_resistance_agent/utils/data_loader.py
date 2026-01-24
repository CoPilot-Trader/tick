"""
Data loader for Support/Resistance Agent.

This module handles loading OHLCV (Open, High, Low, Close, Volume) data from:
1. Mock data (for testing/development)
2. Data Agent (when it's ready)
3. Direct yfinance (fallback option)

Why we need this:
- Separates data loading logic from detection logic
- Makes it easy to switch between mock and real data
- Handles data validation and formatting
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Import yfinance for fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from .logger import get_logger

logger = get_logger(__name__)

if not YFINANCE_AVAILABLE:
    logger.warning("yfinance not available. Install with: pip install yfinance")


class DataLoader:
    """
    Loads OHLCV data from various sources.
    
    This class provides a unified interface for loading data,
    whether it's from mock files, Data Agent, or yfinance.
    """
    
    def __init__(self, use_mock_data: bool = True, data_agent=None):
        """
        Initialize the data loader.
        
        Args:
            use_mock_data: If True, allow mock data as fallback when real data fails. 
                          If False, only use real data sources (Data Agent or yfinance).
            data_agent: Optional Data Agent instance (when it's ready)
        
        Note: The system prioritizes real data (Data Agent → yfinance) and only 
        uses mock data as a final fallback if use_mock_data=True.
        """
        self.use_mock_data = use_mock_data
        self.data_agent = data_agent
        self.mock_data_path = Path(__file__).parent.parent / "tests" / "mocks" / "ohlcv_mock_data.json"
    
    def load_ohlcv_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = "1d"
    ) -> Tuple[pd.DataFrame, str]:
        """
        Load OHLCV data for a symbol.
        
        This is the main method you'll call. It automatically chooses
        the right data source based on availability.
        
        Priority order (real data first, mock as fallback):
        1. Data Agent (if available and configured)
        2. yfinance (real-time data from Yahoo Finance)
        3. Mock data (final fallback if real data fails)
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date for historical data (default: 2 years ago)
            end_date: End date for historical data (default: today)
            timeframe: Data timeframe ("1d", "1h", "4h", etc.)
        
        Returns:
            Tuple of (pandas DataFrame with columns: timestamp, open, high, low, close, volume, data_source)
            data_source: "data_agent", "yfinance", or "mock_data"
        
        Raises:
            FileNotFoundError: If mock data file doesn't exist (only if all sources fail)
            ValueError: If data is invalid
        """
        # Priority 1: Try Data Agent first (if available)
        if self.data_agent:
            logger.info(f"Attempting to load data from Data Agent for {symbol}")
            try:
                df = self._load_from_data_agent(symbol, start_date, end_date, timeframe)
                return df, "data_agent"
            except (NotImplementedError, Exception) as e:
                logger.warning(f"Data Agent failed for {symbol}: {e}. Trying yfinance...")
                # Fall through to yfinance
        
        # Priority 2: Try yfinance (real-time data)
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance is not installed. Skipping real data fetch.")
            if self.use_mock_data:
                logger.info(f"Falling back to mock data for {symbol}")
                df = self._load_mock_data(symbol, start_date, end_date, timeframe)
                return df, "mock_data"
            else:
                raise ImportError(
                    "yfinance is not installed and mock data is disabled. "
                    "Install yfinance with: pip install yfinance"
                )
        
        logger.info(f"Attempting to load real data from yfinance for {symbol}")
        try:
            df = self._load_from_yfinance(symbol, start_date, end_date, timeframe)
            logger.info(f"Successfully loaded {len(df)} data points from yfinance for {symbol}")
            return df, "yfinance"
        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error(f"yfinance failed for {symbol} (timeframe: {timeframe}): {error_msg}")
            
            # Check if it's a minute-level data limitation error
            if timeframe in ["1m", "5m", "15m", "30m"] and ("8 days" in error_msg or "granularity" in error_msg.lower()):
                logger.error(
                    f"yfinance limitation: Minute-level data ({timeframe}) is limited to last 7-8 days. "
                    f"Requested range: {start_date.date()} to {end_date.date()}. "
                    f"This is a yfinance API limitation, not a bug in our code."
                )
            
            logger.debug(f"yfinance error traceback: {traceback.format_exc()}")
            
            # Priority 3: Fallback to mock data (only if real data fails)
            if self.use_mock_data:
                logger.warning(f"Falling back to mock data for {symbol}")
                try:
                    df = self._load_mock_data(symbol, start_date, end_date, timeframe)
                    return df, "mock_data"
                except Exception as mock_error:
                    raise ValueError(
                        f"All data sources failed for {symbol}. "
                        f"yfinance error: {e}, mock data error: {mock_error}"
                    )
            else:
                # No mock data fallback available
                raise ValueError(
                    f"Failed to load data for {symbol} from yfinance: {e}. "
                    f"Mock data fallback is disabled (use_mock_data=False)."
                )
    
    def _load_mock_data(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        timeframe: str
    ) -> pd.DataFrame:
        """
        Load mock OHLCV data from JSON file.
        
        Why mock data?
        - Allows development without Data Agent
        - Consistent test data
        - No API rate limits
        - Fast testing
        """
        if not self.mock_data_path.exists():
            raise FileNotFoundError(
                f"Mock data file not found: {self.mock_data_path}\n"
                "Please create mock OHLCV data first."
            )
        
        # Load JSON file
        with open(self.mock_data_path, 'r') as f:
            mock_data = json.load(f)
        
        # Get data for this symbol
        if symbol not in mock_data:
            raise ValueError(f"Symbol {symbol} not found in mock data")
        
        symbol_data = mock_data[symbol]
        
        # Convert to DataFrame
        df = pd.DataFrame(symbol_data['data'])
        
        # Convert timestamp to datetime (handle timezone)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        # Get available data range
        data_min_date = df['timestamp'].min()
        data_max_date = df['timestamp'].max()
        
        # Filter by date range if provided
        # Convert start_date and end_date to timezone-aware if needed
        if start_date:
            # Make start_date timezone-aware if it's naive
            if start_date.tzinfo is None:
                from datetime import timezone
                start_date = start_date.replace(tzinfo=timezone.utc)
            
            # If requested start_date is after available data, use available data range
            if start_date > data_max_date:
                logger.warning(
                    f"Requested start date {start_date.date()} is after available data. "
                    f"Using available data range: {data_min_date.date()} to {data_max_date.date()}"
                )
                # Use all available data (don't filter by start_date)
            else:
                # Filter by start date
                df = df[df['timestamp'] >= start_date]
        
        if end_date:
            # Make end_date timezone-aware if it's naive
            if end_date.tzinfo is None:
                from datetime import timezone
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            # If requested end_date is before available data, use available data range
            if end_date < data_min_date:
                logger.warning(
                    f"Requested end date {end_date.date()} is before available data. "
                    f"Using available data range: {data_min_date.date()} to {data_max_date.date()}"
                )
                # Use all available data (don't filter by end_date)
            else:
                # Filter by end date
                df = df[df['timestamp'] <= end_date]
        
        # Final check: if no data after filtering, use most recent data (for mock data compatibility)
        if len(df) == 0:
            logger.warning(
                f"No data in requested range for {symbol}. "
                f"Using most recent {min(730, len(symbol_data['data']))} data points from available range: "
                f"{data_min_date.date()} to {data_max_date.date()}"
            )
            # Use most recent data points (up to 730 days worth)
            df = pd.DataFrame(symbol_data['data'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df = df.sort_values('timestamp', ascending=False).head(730).sort_values('timestamp').reset_index(drop=True)
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Validate data
        self._validate_data(df, symbol)
        
        logger.info(f"Loaded {len(df)} data points for {symbol}")
        return df
    
    def _load_from_data_agent(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        timeframe: str
    ) -> pd.DataFrame:
        """
        Load data from Data Agent.
        
        This will be implemented when Data Agent is ready.
        For now, it raises NotImplementedError.
        """
        # TODO: Implement when Data Agent is ready
        # Example:
        # response = self.data_agent.fetch_historical(
        #     symbol=symbol,
        #     start_date=start_date or (datetime.now() - timedelta(days=730)),
        #     end_date=end_date or datetime.now(),
        #     timeframe=timeframe
        # )
        # return self._convert_to_dataframe(response['data'])
        
        raise NotImplementedError(
            "Data Agent integration not yet available. "
            "Use mock data for now (set use_mock_data=True)."
        )
    
    def _load_from_yfinance(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        timeframe: str
    ) -> pd.DataFrame:
        """
        Load OHLCV data from yfinance (Yahoo Finance).
        
        This is a fallback option when Data Agent is not available.
        yfinance provides free historical stock data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            start_date: Start date for historical data
            end_date: End date for historical data
            timeframe: Data timeframe ("1d", "1h", "4h", etc.)
        
        Returns:
            pandas DataFrame with columns: timestamp, open, high, low, close, volume
        
        Raises:
            ImportError: If yfinance is not installed
            ValueError: If symbol is invalid or data cannot be fetched
        """
        if not YFINANCE_AVAILABLE:
            raise ImportError(
                "yfinance is not installed. Install with: pip install yfinance. "
                "The system will automatically fall back to mock data if available."
            )
        
        try:
            # Set default dates if not provided
            from datetime import timezone
            if end_date is None:
                end_date = datetime.now(timezone.utc)
            else:
                # Ensure end_date is not in the future
                now = datetime.now(timezone.utc)
                if end_date > now:
                    logger.warning(f"end_date {end_date} is in the future. Adjusting to now: {now}")
                    end_date = now
            
            if start_date is None:
                start_date = end_date - timedelta(days=730)  # 2 years default
            else:
                # Ensure start_date is not after end_date
                if start_date > end_date:
                    logger.warning(f"start_date {start_date} is after end_date {end_date}. Adjusting start_date.")
                    start_date = end_date - timedelta(days=1)
            
            # Convert timeframe to yfinance interval
            # yfinance uses: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            # Note: yfinance doesn't support 4h directly, use 1h for hourly data
            interval_map = {
                "1m": "1m",      # 1 minute
                "5m": "5m",      # 5 minutes
                "15m": "15m",    # 15 minutes
                "30m": "30m",    # 30 minutes
                "1h": "1h",      # 1 hour
                "4h": "1h",      # 4h not supported, use 1h (will filter later if needed)
                "1d": "1d",      # 1 day
                "1w": "1wk",     # 1 week
                "1mo": "1mo",    # 1 month
                "1y": "1mo"      # 1 year - yfinance doesn't support "1y", use monthly data
            }
            interval = interval_map.get(timeframe, "1d")
            logger.debug(f"Using yfinance interval '{interval}' for timeframe '{timeframe}'")
            
            # yfinance limitations for minute-level data:
            # - 1m, 5m, 15m, 30m: Only last 7-8 days available
            # - 1h: Only last 60 days available
            # - 4h: Not directly supported, use 1h
            # - Daily and above: Years of data available
            minute_timeframes = ["1m", "5m", "15m", "30m"]
            hourly_timeframes = ["1h", "4h"]
            
            # Adjust start_date if requesting too much history for minute/hourly data
            if timeframe in minute_timeframes:
                max_days = 5  # yfinance limit: ~7-8 days, but use 5 to be safe
                min_start_date = end_date - timedelta(days=max_days)
                if start_date < min_start_date:
                    logger.warning(
                        f"yfinance only provides last {max_days} days for {timeframe} data. "
                        f"Adjusting start_date from {start_date.date()} to {min_start_date.date()}"
                    )
                    start_date = min_start_date
            elif timeframe in hourly_timeframes:
                max_days = 60  # yfinance limit: ~60 days for hourly data
                min_start_date = end_date - timedelta(days=max_days)
                if start_date < min_start_date:
                    logger.warning(
                        f"yfinance only provides last {max_days} days for {timeframe} data. "
                        f"Adjusting start_date from {start_date.date()} to {min_start_date.date()}"
                    )
                    start_date = min_start_date
            
            logger.info(f"Fetching {symbol} data from yfinance: {start_date.date()} to {end_date.date()} (interval: {interval})")
            
            # Download data from yfinance
            ticker = yf.Ticker(symbol)
            
            # For minute-level data, yfinance can be finicky - try with period instead of start/end
            if timeframe in minute_timeframes:
                # Use period parameter for minute data (more reliable)
                try:
                    # Try with period first (last 5 days)
                    df = ticker.history(
                        period="5d",
                        interval=interval,
                        auto_adjust=True,
                        prepost=False
                    )
                    logger.info(f"Successfully fetched minute data using period='5d'")
                except Exception as period_error:
                    logger.warning(f"Period method failed: {period_error}. Trying start/end dates...")
                    # Fallback to start/end dates
                    df = ticker.history(
                        start=start_date,
                        end=end_date,
                        interval=interval,
                        auto_adjust=True,
                        prepost=False
                    )
            else:
                # For other timeframes, use start/end dates normally
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    auto_adjust=True,
                    prepost=False
                )
            
            if df.empty:
                raise ValueError(f"No data returned from yfinance for {symbol} (timeframe: {timeframe}, interval: {interval})")
            
            # Rename columns to match our format (yfinance uses different names)
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Reset index to get Date as a column
            df = df.reset_index()
            df = df.rename(columns={'Date': 'timestamp'})
            
            # Ensure timestamp is timezone-aware (yfinance returns timezone-aware)
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            else:
                df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            
            # Select only required columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
            
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Validate data
            self._validate_data(df, symbol)
            
            logger.info(f"Successfully loaded {len(df)} data points for {symbol} from yfinance")
            return df
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Failed to load data from yfinance for {symbol}: {e}")
            logger.debug(f"yfinance error details: {error_details}")
            # Don't fall back here - let the main load_ohlcv_data method handle fallback
            raise ValueError(f"yfinance failed to load data for {symbol}: {e}")
    
    def _validate_data(self, df: pd.DataFrame, symbol: str) -> None:
        """
        Validate OHLCV data quality.
        
        Checks:
        - Required columns exist
        - No missing values
        - Data types are correct
        - Price values are positive
        - High >= Low (logical check)
        """
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        # Check required columns
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Check for missing values
        if df[required_columns].isnull().any().any():
            missing_count = df[required_columns].isnull().sum().sum()
            logger.warning(f"Found {missing_count} missing values in {symbol} data")
        
        # Check data types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column {col} must be numeric")
        
        # Check price values are positive
        price_columns = ['open', 'high', 'low', 'close']
        if (df[price_columns] <= 0).any().any():
            raise ValueError(f"Price values must be positive for {symbol}")
        
        # Check High >= Low (logical check)
        if (df['high'] < df['low']).any():
            invalid_rows = (df['high'] < df['low']).sum()
            raise ValueError(f"Found {invalid_rows} rows where high < low for {symbol}")
        
        logger.debug(f"Data validation passed for {symbol}")
    
    def _convert_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert data from Data Agent format to pandas DataFrame.
        
        This will be used when Data Agent is ready.
        """
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp').reset_index(drop=True)
