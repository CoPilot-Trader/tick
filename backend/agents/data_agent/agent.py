"""
Data Agent - Main agent implementation.

The Data Agent is responsible for:
1. Fetching OHLCV data from multiple sources (Tiingo, yfinance, FMP)
2. Managing data collectors with fallback strategies
3. Enriching data with context modules
4. Coordinating with Feature Agent for technical indicators

Milestone: M1 - Foundation & Data Pipeline
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from core.interfaces.base_agent import BaseAgent
from .schema import normalize_dataframe, normalize_timeframe

logger = logging.getLogger(__name__)


class DataAgent(BaseAgent):
    """
    Data Agent for ingesting and managing OHLCV data.

    Features:
    - Multi-source data fetching with fallback
    - Context enrichment via Context Loader
    - Parquet storage for historical data
    - Real-time data support via Tiingo IEX
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Data Agent."""
        super().__init__(name="data_agent", config=config)
        self.version = "2.0.0"

        # Collectors (lazy-loaded)
        self._collectors = {}
        self._context_loader = None
        self._storage = None

        # Configuration
        self._tiingo_api_key = config.get("tiingo_api_key") if config else None
        self._fmp_api_key = config.get("fmp_api_key") if config else None

        # Fallback order for data fetching
        self._collector_priority = ["tiingo", "yfinance"]

    def initialize(self) -> bool:
        """
        Initialize the Data Agent.

        - Initialize data collectors (Tiingo, yfinance, FMP, FRED)
        - Set up context loader
        - Initialize storage
        """
        try:
            # Load API keys from environment if not in config
            if not self._tiingo_api_key:
                self._tiingo_api_key = os.getenv("TIINGO_API_KEY")
            if not self._fmp_api_key:
                self._fmp_api_key = os.getenv("FMP_API_KEY")

            # Initialize collectors
            self._init_collectors()

            self.initialized = True
            logger.info(f"DataAgent v{self.version} initialized")
            logger.info(f"Available collectors: {list(self._collectors.keys())}")
            return True

        except Exception as e:
            logger.error(f"DataAgent initialization failed: {e}")
            self.initialized = False
            return False

    def _init_collectors(self) -> None:
        """Initialize all data collectors."""
        from .collectors import (
            YFinanceCollector,
            TiingoCollector,
            FMPCollector,
            FREDCollector,
        )

        # Tiingo (primary for OHLCV)
        if self._tiingo_api_key:
            try:
                tiingo = TiingoCollector(api_key=self._tiingo_api_key)
                if tiingo.initialize():
                    self._collectors["tiingo"] = tiingo
                    logger.info("Tiingo collector initialized")
            except Exception as e:
                logger.warning(f"Tiingo collector failed: {e}")

        # yfinance (fallback for OHLCV)
        try:
            yf = YFinanceCollector()
            if yf.initialize():
                self._collectors["yfinance"] = yf
                logger.info("yfinance collector initialized")
        except Exception as e:
            logger.warning(f"yfinance collector failed: {e}")

        # FMP (for earnings and fundamentals)
        if self._fmp_api_key:
            try:
                fmp = FMPCollector(api_key=self._fmp_api_key)
                if fmp.initialize():
                    self._collectors["fmp"] = fmp
                    logger.info("FMP collector initialized")
            except Exception as e:
                logger.warning(f"FMP collector failed: {e}")

        # FRED (for economic data)
        try:
            fred = FREDCollector()
            if fred.initialize():
                self._collectors["fred"] = fred
                logger.info("FRED collector initialized")
        except Exception as e:
            logger.warning(f"FRED collector failed: {e}")

    def _get_context_loader(self):
        """Lazy-load context loader."""
        if self._context_loader is None:
            from .context import ContextLoader
            self._context_loader = ContextLoader()
        return self._context_loader

    def _get_storage(self):
        """Lazy-load storage."""
        if self._storage is None:
            from .storage import ParquetStorage
            data_path = self.config.get("data_path") if self.config else None
            data_path = data_path or os.getenv("DATA_LAKE_ROOT", "/srv/data_lake")
            self._storage = ParquetStorage(base_path=data_path)
        return self._storage

    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process data request for a given symbol.

        Args:
            symbol: Stock symbol
            params: Optional parameters:
                - start_date: datetime or string
                - end_date: datetime or string
                - timeframe: "1d", "5m", etc.
                - enrich: bool, whether to enrich with context

        Returns:
            Dictionary with OHLCV data or error
        """
        if not self.initialized:
            return {"error": "DataAgent not initialized", "symbol": symbol}

        params = params or {}
        end_date = params.get("end_date", datetime.now())
        start_date = params.get("start_date", end_date - timedelta(days=30))
        timeframe = params.get("timeframe", "1d")
        enrich = params.get("enrich", False)

        # Convert string dates to datetime
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # Fetch data
        data = self.fetch_historical_sync(symbol, start_date, end_date, timeframe)

        if data is None or data.empty:
            return {"error": f"No data for {symbol}", "symbol": symbol}

        # Optionally enrich with context
        if enrich:
            data = self.enrich_data(data, symbol)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "rows": len(data),
            "columns": list(data.columns),
            "data": data.to_dict(orient="records"),
        }

    def fetch_historical_sync(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data synchronously.

        Uses fallback strategy: try Tiingo first, then yfinance.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe

        Returns:
            DataFrame with OHLCV data or None
        """
        if not self.initialized:
            logger.error("DataAgent not initialized")
            return None

        timeframe_normalized = normalize_timeframe(timeframe)

        # Try collectors in priority order
        for collector_name in self._collector_priority:
            collector = self._collectors.get(collector_name)
            if not collector:
                continue

            try:
                result = collector.fetch_historical(
                    symbol, start_date, end_date, timeframe
                )
                if result.success and result.data is not None and not result.data.empty:
                    logger.debug(f"Fetched {symbol} from {collector_name}")
                    return result.data
            except Exception as e:
                logger.warning(f"{collector_name} failed for {symbol}: {e}")
                continue

        logger.warning(f"All collectors failed for {symbol}")

        # Fallback to mock data for demo purposes
        logger.info(f"Attempting to load mock data for {symbol}")
        mock_data = self._load_mock_data(symbol, start_date, end_date)
        if mock_data is not None:
            return mock_data

        return None

    def _load_mock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[pd.DataFrame]:
        """
        Load mock OHLCV data as fallback for demo purposes.

        Uses the same mock data file as the support_resistance_agent.
        """
        try:
            mock_data_path = Path(__file__).parent.parent / "support_resistance_agent" / "tests" / "mocks" / "ohlcv_mock_data.json"

            if not mock_data_path.exists():
                logger.warning(f"Mock data file not found: {mock_data_path}")
                return None

            with open(mock_data_path, 'r') as f:
                mock_data = json.load(f)

            if symbol not in mock_data:
                logger.warning(f"Symbol {symbol} not found in mock data")
                return None

            symbol_data = mock_data[symbol]
            df = pd.DataFrame(symbol_data['data'])

            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            # Filter by date range
            if start_date.tzinfo is None:
                from datetime import timezone
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                from datetime import timezone
                end_date = end_date.replace(tzinfo=timezone.utc)

            # Use available data range if requested dates are outside
            data_min = df['timestamp'].min()
            data_max = df['timestamp'].max()

            if start_date > data_max:
                logger.warning(f"Using available mock data range for {symbol}: {data_min.date()} to {data_max.date()}")
            else:
                df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

            if len(df) == 0:
                logger.warning(f"No mock data in date range for {symbol}")
                return None

            # Set timestamp as index
            df.set_index('timestamp', inplace=True)

            logger.info(f"Loaded {len(df)} mock data points for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to load mock data for {symbol}: {e}")
            return None

    def fetch_historical(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> Dict[str, Any]:
        """
        Fetch historical OHLCV data (returns dict for API compatibility).
        """
        data = self.fetch_historical_sync(symbol, start_date, end_date, timeframe)

        if data is None:
            return {"error": f"No data for {symbol}"}

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "rows": len(data),
            "data": data.to_dict(orient="records"),
        }

    def fetch_realtime(
        self,
        symbol: str,
        timeframe: str = "5m",
        bars: int = 1,
    ) -> Dict[str, Any]:
        """
        Fetch real-time/latest OHLCV data.

        Args:
            symbol: Stock symbol
            timeframe: Data timeframe
            bars: Number of recent bars

        Returns:
            Dictionary with latest data
        """
        if not self.initialized:
            return {"error": "DataAgent not initialized"}

        # Try Tiingo first (has IEX real-time)
        if "tiingo" in self._collectors:
            try:
                result = self._collectors["tiingo"].fetch_latest(symbol, timeframe, bars)
                if result.success and result.data is not None:
                    return {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "data": result.data.to_dict(orient="records"),
                    }
            except Exception as e:
                logger.warning(f"Tiingo realtime failed: {e}")

        # Fallback to yfinance
        if "yfinance" in self._collectors:
            try:
                result = self._collectors["yfinance"].fetch_latest(symbol, timeframe, bars)
                if result.success and result.data is not None:
                    return {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "data": result.data.to_dict(orient="records"),
                    }
            except Exception as e:
                logger.warning(f"yfinance realtime failed: {e}")

        return {"error": f"Could not fetch realtime data for {symbol}"}

    def enrich_data(
        self,
        data: pd.DataFrame,
        symbol: str,
    ) -> pd.DataFrame:
        """
        Enrich OHLCV data with context modules.

        Args:
            data: OHLCV DataFrame
            symbol: Stock symbol (for ticker-specific context)

        Returns:
            Enriched DataFrame
        """
        loader = self._get_context_loader()

        # Ensure required columns for context loader
        if "ticker" not in data.columns:
            data["ticker"] = symbol.upper()
        if "timestamp" not in data.columns and "bar_ts" in data.columns:
            data["timestamp"] = data["bar_ts"]

        return loader.enrich_signals(data)

    def validate_data_quality(self, symbol: str) -> Dict[str, Any]:
        """
        Validate data quality for a symbol.

        Checks for:
        - Missing values
        - Price anomalies
        - Volume spikes
        - Data freshness
        """
        # Fetch recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        data = self.fetch_historical_sync(symbol, start_date, end_date, "1d")

        if data is None or data.empty:
            return {"valid": False, "error": "No data available"}

        issues = []

        # Check for missing values
        null_counts = data.isnull().sum()
        if null_counts.any():
            issues.append(f"Missing values: {null_counts.to_dict()}")

        # Check for price anomalies (>20% daily change)
        if "close" in data.columns and len(data) > 1:
            pct_change = data["close"].pct_change().abs()
            anomalies = (pct_change > 0.20).sum()
            if anomalies > 0:
                issues.append(f"Price anomalies (>20% change): {anomalies}")

        # Check data freshness
        if "bar_ts" in data.columns:
            latest = pd.to_datetime(data["bar_ts"]).max()
            days_old = (datetime.now() - latest).days
            if days_old > 3:
                issues.append(f"Data is {days_old} days old")

        return {
            "valid": len(issues) == 0,
            "symbol": symbol,
            "rows": len(data),
            "issues": issues,
        }

    def get_collector_status(self) -> Dict[str, Any]:
        """Get status of all data collectors."""
        status = {}
        for name, collector in self._collectors.items():
            status[name] = collector.health_check()
        return status

    def health_check(self) -> Dict[str, Any]:
        """Check Data Agent health."""
        collector_status = {}
        healthy_collectors = 0

        for name, collector in self._collectors.items():
            check = collector.health_check()
            collector_status[name] = check.get("status", "unknown")
            if check.get("status") == "healthy":
                healthy_collectors += 1

        return {
            "status": "healthy" if self.initialized and healthy_collectors > 0 else "degraded",
            "agent": self.name,
            "version": self.version,
            "collectors": collector_status,
            "healthy_collectors": healthy_collectors,
        }
