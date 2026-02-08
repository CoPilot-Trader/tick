"""
Feature Agent - Main agent implementation.

The Feature Agent is responsible for:
1. Calculating technical indicators (momentum, volatility, trend, volume)
2. Engineering features from OHLCV data
3. Providing both batch and incremental calculation modes

Milestone: M1 - Foundation & Data Pipeline
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from core.interfaces.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FeatureAgent(BaseAgent):
    """
    Feature Agent for computing technical indicators and engineered features.

    Supports:
    - Momentum indicators (RSI, MACD, Stochastic, CCI, MFI)
    - Volatility indicators (ATR, Bollinger Bands)
    - Trend indicators (ADX, moving averages)
    - Volume indicators (OBV, VWAP)
    - Time-based features (day of week, hour of day)

    Features:
    - calculate_all(): Compute all indicators on a DataFrame
    - calculate_incremental(): Efficient calculation for real-time
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Feature Agent."""
        super().__init__(name="feature_agent", config=config)
        self.version = "2.0.0"

        # Indicator modules (lazy-loaded)
        self._momentum = None
        self._volatility = None
        self._trend = None
        self._volume = None
        self._time_features = None

    def initialize(self) -> bool:
        """
        Initialize the Feature Agent.

        - Import indicator modules
        - Verify dependencies (pandas, numpy)
        """
        try:
            # Verify pandas/numpy available
            import pandas as pd
            import numpy as np

            self.initialized = True
            logger.info(f"FeatureAgent v{self.version} initialized")
            return True

        except Exception as e:
            logger.error(f"FeatureAgent initialization failed: {e}")
            self.initialized = False
            return False

    def _load_momentum(self):
        """Lazy-load momentum indicators."""
        if self._momentum is None:
            from .indicators import momentum
            self._momentum = momentum
        return self._momentum

    def _load_volatility(self):
        """Lazy-load volatility indicators."""
        if self._volatility is None:
            from .indicators import volatility
            self._volatility = volatility
        return self._volatility

    def _load_trend(self):
        """Lazy-load trend indicators."""
        if self._trend is None:
            from .indicators import trend
            self._trend = trend
        return self._trend

    def _load_volume(self):
        """Lazy-load volume indicators."""
        if self._volume is None:
            from .indicators import volume
            self._volume = volume
        return self._volume

    def _load_time_features(self):
        """Lazy-load time features."""
        if self._time_features is None:
            from .indicators import time_features
            self._time_features = time_features
        return self._time_features

    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process feature calculation for a given symbol.

        Args:
            symbol: Stock symbol
            params: Optional parameters:
                - data: DataFrame with OHLCV data
                - indicators: List of indicators to calculate

        Returns:
            Dictionary with calculated features
        """
        if not self.initialized:
            return {"error": "FeatureAgent not initialized", "symbol": symbol}

        params = params or {}
        data = params.get("data")

        if data is None:
            return {"error": "No data provided", "symbol": symbol}

        # Convert to DataFrame if dict
        if isinstance(data, dict):
            data = pd.DataFrame(data)

        # Calculate all indicators
        result = self.calculate_all(data)

        return {
            "symbol": symbol,
            "rows": len(result),
            "columns": list(result.columns),
            "data": result.to_dict(orient="records"),
        }

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators on a DataFrame.

        Args:
            df: DataFrame with OHLCV columns (open, high, low, close, volume)

        Returns:
            DataFrame with all indicators added
        """
        if df is None or df.empty:
            return df

        result = df.copy()

        # Ensure lowercase columns
        result.columns = result.columns.str.lower()

        # Check required columns
        required = ["open", "high", "low", "close"]
        missing = [c for c in required if c not in result.columns]
        if missing:
            logger.warning(f"Missing columns for indicators: {missing}")
            return result

        try:
            # Momentum indicators
            momentum = self._load_momentum()
            if momentum and "close" in result.columns:
                result["rsi_14"] = momentum.calc_rsi(result["close"], period=14)

                macd, signal, hist = momentum.calc_macd(result["close"])
                result["macd"] = macd
                result["macd_signal"] = signal
                result["macd_hist"] = hist

                if all(c in result.columns for c in ["high", "low", "close"]):
                    stoch_k, stoch_d = momentum.calc_stochastic(result)
                    result["stoch_k"] = stoch_k
                    result["stoch_d"] = stoch_d

                    result["cci_20"] = momentum.calc_cci(result)
                    result["williams_r"] = momentum.calc_williams_r(result)

                    if "volume" in result.columns:
                        result["mfi_14"] = momentum.calc_mfi(result)

        except Exception as e:
            logger.warning(f"Momentum indicators failed: {e}")

        try:
            # Volatility indicators
            volatility = self._load_volatility()
            if volatility and all(c in result.columns for c in ["high", "low", "close"]):
                result["atr_14"] = volatility.calc_atr(result, period=14)

                bb_middle, bb_upper, bb_lower = volatility.calc_bollinger_bands(
                    result["close"], period=20
                )
                result["bb_upper"] = bb_upper
                result["bb_middle"] = bb_middle
                result["bb_lower"] = bb_lower
                result["bb_width"] = (bb_upper - bb_lower) / bb_middle

        except Exception as e:
            logger.warning(f"Volatility indicators failed: {e}")

        try:
            # Trend indicators
            trend = self._load_trend()
            if trend and all(c in result.columns for c in ["high", "low", "close"]):
                result["adx_14"] = trend.calc_adx(result, period=14)
                result["sma_20"] = trend.calc_sma(result["close"], period=20)
                result["sma_50"] = trend.calc_sma(result["close"], period=50)
                result["ema_12"] = trend.calc_ema(result["close"], period=12)
                result["ema_26"] = trend.calc_ema(result["close"], period=26)

        except Exception as e:
            logger.warning(f"Trend indicators failed: {e}")

        try:
            # Volume indicators
            volume = self._load_volume()
            if volume and "close" in result.columns and "volume" in result.columns:
                result["obv"] = volume.calc_obv(result)

                if all(c in result.columns for c in ["high", "low", "close", "volume"]):
                    result["vwap"] = volume.calc_vwap(result)
                    result["volume_sma_20"] = volume.calc_volume_ma(result, period=20)
                    result["relative_volume"] = result["volume"] / result["volume_sma_20"]

        except Exception as e:
            logger.warning(f"Volume indicators failed: {e}")

        try:
            # Time-based features
            time_features = self._load_time_features()
            if time_features:
                # Check for timestamp column
                ts_col = None
                for col in ["timestamp", "bar_ts", "date", "datetime"]:
                    if col in result.columns:
                        ts_col = col
                        break

                if ts_col:
                    # Convert timestamp column to index for time features
                    temp_df = result.copy()
                    temp_df.index = pd.to_datetime(temp_df[ts_col])
                    time_result = time_features.add_time_features(temp_df)
                    # Copy time feature columns back
                    for col in time_result.columns:
                        if col not in result.columns:
                            result[col] = time_result[col].values

        except Exception as e:
            logger.warning(f"Time features failed: {e}")

        return result

    def calculate_incremental(self, recent_bars: List[Dict]) -> Dict[str, Any]:
        """
        Calculate indicators on recent data for real-time inference.

        More efficient than calculate_all() for streaming data.

        Args:
            recent_bars: List of recent OHLCV bars (as dicts)

        Returns:
            Dict with latest indicator values
        """
        if not recent_bars:
            return {}

        df = pd.DataFrame(recent_bars)
        result = self.calculate_all(df)

        if result.empty:
            return {}

        # Return only the latest row as a dict
        return result.iloc[-1].to_dict()

    def calculate_indicators(self, ohlcv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate technical indicators from OHLCV data (dict format).

        Args:
            ohlcv_data: Dict with 'data' key containing OHLCV records

        Returns:
            Dict with calculated indicators
        """
        data = ohlcv_data.get("data", [])
        if not data:
            return {"error": "No data provided"}

        df = pd.DataFrame(data)
        result = self.calculate_all(df)

        return {
            "rows": len(result),
            "columns": list(result.columns),
            "data": result.to_dict(orient="records"),
        }

    def engineer_features(
        self,
        ohlcv_data: Dict[str, Any],
        indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Engineer features from OHLCV data and indicators.

        Combines raw OHLCV with indicators and adds derived features.

        Args:
            ohlcv_data: OHLCV data dict
            indicators: Indicators dict

        Returns:
            Dict with engineered features
        """
        # Merge OHLCV with indicators
        ohlcv_df = pd.DataFrame(ohlcv_data.get("data", []))
        ind_df = pd.DataFrame(indicators.get("data", []))

        if ohlcv_df.empty:
            return {"error": "No OHLCV data"}

        # If indicators provided, merge them
        if not ind_df.empty:
            result = pd.concat([ohlcv_df, ind_df], axis=1)
            # Remove duplicate columns
            result = result.loc[:, ~result.columns.duplicated()]
        else:
            result = ohlcv_df

        # Add derived features
        if "close" in result.columns:
            result["returns_1d"] = result["close"].pct_change()
            result["returns_5d"] = result["close"].pct_change(5)
            result["log_returns"] = np.log(result["close"] / result["close"].shift(1))

        if "high" in result.columns and "low" in result.columns:
            result["daily_range"] = result["high"] - result["low"]
            result["daily_range_pct"] = result["daily_range"] / result["close"]

        return {
            "rows": len(result),
            "columns": list(result.columns),
            "data": result.to_dict(orient="records"),
        }

    def get_indicator_list(self) -> List[str]:
        """Get list of available indicators."""
        return [
            # Momentum
            "rsi_14", "macd", "macd_signal", "macd_hist",
            "stoch_k", "stoch_d", "cci_20", "williams_r", "mfi_14",
            # Volatility
            "atr_14", "bb_upper", "bb_middle", "bb_lower", "bb_width",
            # Trend
            "adx_14", "sma_20", "sma_50", "ema_12", "ema_26",
            # Volume
            "obv", "vwap", "volume_sma_20", "relative_volume",
            # Time
            "day_of_week", "hour", "is_market_hours",
        ]

    def health_check(self) -> Dict[str, Any]:
        """Check Feature Agent health."""
        # Test indicator calculation
        test_success = False
        try:
            test_df = pd.DataFrame({
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            })
            result = self.calculate_all(test_df)
            test_success = len(result.columns) > 5
        except Exception:
            pass

        return {
            "status": "healthy" if self.initialized and test_success else "degraded",
            "agent": self.name,
            "version": self.version,
            "indicators_available": len(self.get_indicator_list()),
            "test_passed": test_success,
        }
