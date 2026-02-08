"""
Feature Builder for Trend Classification.

Provides feature engineering specifically designed for
BUY/SELL/HOLD classification tasks.
"""

import logging
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """
    Feature engineering for trend classification.

    Creates features specifically designed for predicting
    directional price movements.

    Feature Categories:
    - Momentum features
    - Trend features
    - Volatility features
    - Volume features
    - Pattern features
    """

    # Default feature groups
    FEATURE_GROUPS = {
        "momentum": [
            "rsi_14", "macd", "macd_signal", "macd_histogram",
            "stoch_k", "stoch_d", "cci_20", "williams_r", "mfi_14",
            "momentum_5d", "momentum_10d", "momentum_20d",
        ],
        "trend": [
            "adx_14", "price_sma_ratio", "price_ema_ratio",
            "sma_cross", "ema_cross", "trend_strength",
        ],
        "volatility": [
            "atr_14", "bb_position", "bb_width",
            "volatility_ratio", "historical_volatility",
        ],
        "volume": [
            "volume_ratio", "obv_signal", "vwap_distance",
            "volume_trend",
        ],
        "returns": [
            "returns_1d", "returns_5d", "returns_10d", "returns_20d",
            "log_returns", "cumulative_returns_5d",
        ],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Feature Builder.

        Args:
            config: Configuration dict
                - feature_groups: List of feature groups to use
                - custom_features: List of custom feature names
        """
        self.config = config or {}
        self.feature_groups = self.config.get(
            "feature_groups",
            list(self.FEATURE_GROUPS.keys())
        )
        self.custom_features = self.config.get("custom_features", [])

    def build_features(
        self,
        df: pd.DataFrame,
        add_derived: bool = True
    ) -> pd.DataFrame:
        """
        Build all classification features.

        Args:
            df: Input DataFrame with OHLCV data
            add_derived: Add derived features on top of existing

        Returns:
            DataFrame with all features
        """
        df_feat = df.copy()

        # Add momentum features
        if "momentum" in self.feature_groups:
            df_feat = self._add_momentum_features(df_feat)

        # Add trend features
        if "trend" in self.feature_groups:
            df_feat = self._add_trend_features(df_feat)

        # Add volatility features
        if "volatility" in self.feature_groups:
            df_feat = self._add_volatility_features(df_feat)

        # Add volume features
        if "volume" in self.feature_groups:
            df_feat = self._add_volume_features(df_feat)

        # Add return features
        if "returns" in self.feature_groups:
            df_feat = self._add_return_features(df_feat)

        # Add pattern features
        if add_derived:
            df_feat = self._add_pattern_features(df_feat)

        return df_feat

    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum-based features."""
        close = df["close"]

        # Momentum over different periods
        if "momentum_5d" not in df.columns:
            df["momentum_5d"] = close / close.shift(5) - 1

        if "momentum_10d" not in df.columns:
            df["momentum_10d"] = close / close.shift(10) - 1

        if "momentum_20d" not in df.columns:
            df["momentum_20d"] = close / close.shift(20) - 1

        # Rate of change
        df["roc_5d"] = (close - close.shift(5)) / close.shift(5) * 100
        df["roc_10d"] = (close - close.shift(10)) / close.shift(10) * 100

        # Momentum acceleration
        mom_5 = close - close.shift(5)
        df["momentum_accel"] = mom_5 - mom_5.shift(5)

        # RSI normalized (if exists)
        if "rsi_14" in df.columns:
            df["rsi_normalized"] = (df["rsi_14"] - 50) / 50

        # MACD histogram slope
        if "macd_histogram" in df.columns:
            df["macd_hist_slope"] = df["macd_histogram"] - df["macd_histogram"].shift(1)

        return df

    def _add_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend-based features."""
        close = df["close"]

        # Price relative to moving averages
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()

        df["price_sma_20_ratio"] = close / sma_20
        df["price_sma_50_ratio"] = close / sma_50
        df["price_ema_12_ratio"] = close / ema_12
        df["price_ema_26_ratio"] = close / ema_26

        # MA crossover signals
        df["sma_20_50_ratio"] = sma_20 / sma_50
        df["ema_12_26_ratio"] = ema_12 / ema_26

        # Trend direction (1 = up, -1 = down, 0 = neutral)
        df["trend_direction"] = np.sign(close - sma_20)

        # Trend strength (distance from MA as % of price)
        df["trend_strength_20"] = (close - sma_20) / close
        df["trend_strength_50"] = (close - sma_50) / close

        # Number of up days in last N days
        daily_change = close.diff()
        df["up_days_5"] = (daily_change > 0).rolling(5).sum()
        df["up_days_10"] = (daily_change > 0).rolling(10).sum()
        df["up_days_20"] = (daily_change > 0).rolling(20).sum()

        # Consecutive up/down days
        df["up_streak"] = self._calc_streak(daily_change > 0)
        df["down_streak"] = self._calc_streak(daily_change < 0)

        return df

    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility-based features."""
        close = df["close"]
        high = df["high"] if "high" in df.columns else close
        low = df["low"] if "low" in df.columns else close

        # Historical volatility
        returns = close.pct_change()
        df["volatility_5d"] = returns.rolling(5).std()
        df["volatility_10d"] = returns.rolling(10).std()
        df["volatility_20d"] = returns.rolling(20).std()

        # Volatility ratio (short vs long)
        if df["volatility_20d"].notna().any():
            df["volatility_ratio"] = df["volatility_5d"] / df["volatility_20d"]

        # True Range
        df["true_range"] = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - close.shift(1)),
                np.abs(low - close.shift(1))
            )
        )

        # ATR normalized
        if "atr_14" in df.columns:
            df["atr_pct"] = df["atr_14"] / close

        # Bollinger Band position (where is price within bands)
        if all(c in df.columns for c in ["bb_upper", "bb_lower"]):
            bb_range = df["bb_upper"] - df["bb_lower"]
            df["bb_position"] = np.where(
                bb_range > 0,
                (close - df["bb_lower"]) / bb_range,
                0.5
            )

        # High-low range as % of close
        df["hl_range_pct"] = (high - low) / close

        return df

    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features."""
        if "volume" not in df.columns:
            return df

        volume = df["volume"]
        close = df["close"]

        # Volume moving averages
        vol_sma_5 = volume.rolling(5).mean()
        vol_sma_20 = volume.rolling(20).mean()

        df["volume_ratio_5"] = volume / vol_sma_5
        df["volume_ratio_20"] = volume / vol_sma_20

        # Volume trend
        df["volume_trend"] = vol_sma_5 / vol_sma_20

        # Price-volume trend
        df["pv_trend"] = (close.pct_change() * volume).rolling(5).sum()

        # Volume on up vs down days
        up_mask = close.diff() > 0
        down_mask = close.diff() < 0

        up_volume = volume.where(up_mask, 0).rolling(10).sum()
        down_volume = volume.where(down_mask, 0).rolling(10).sum()

        df["volume_ratio_updown"] = np.where(
            down_volume > 0,
            up_volume / down_volume,
            1.0
        )

        # Money flow
        typical_price = (df["high"] + df["low"] + close) / 3 if all(c in df.columns for c in ["high", "low"]) else close
        money_flow = typical_price * volume
        df["money_flow_5d"] = money_flow.rolling(5).sum()

        return df

    def _add_return_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add return-based features."""
        close = df["close"]

        # Simple returns
        if "returns_1d" not in df.columns:
            df["returns_1d"] = close.pct_change(1)
        if "returns_5d" not in df.columns:
            df["returns_5d"] = close.pct_change(5)
        if "returns_10d" not in df.columns:
            df["returns_10d"] = close.pct_change(10)
        if "returns_20d" not in df.columns:
            df["returns_20d"] = close.pct_change(20)

        # Log returns
        df["log_returns"] = np.log(close / close.shift(1))

        # Cumulative returns
        df["cum_returns_5d"] = (1 + df["returns_1d"]).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
        df["cum_returns_10d"] = (1 + df["returns_1d"]).rolling(10).apply(lambda x: np.prod(x) - 1, raw=True)

        # Return skewness
        df["return_skew_20d"] = df["returns_1d"].rolling(20).skew()

        # Return z-score
        rolling_mean = df["returns_1d"].rolling(20).mean()
        rolling_std = df["returns_1d"].rolling(20).std()
        df["return_zscore"] = (df["returns_1d"] - rolling_mean) / rolling_std

        return df

    def _add_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add pattern-based features."""
        close = df["close"]
        high = df["high"] if "high" in df.columns else close
        low = df["low"] if "low" in df.columns else close
        open_price = df["open"] if "open" in df.columns else close.shift(1)

        # Candle body (relative to range)
        candle_range = high - low
        df["candle_body"] = np.where(
            candle_range > 0,
            (close - open_price) / candle_range,
            0
        )

        # Upper/lower shadows
        df["upper_shadow"] = np.where(
            candle_range > 0,
            (high - np.maximum(close, open_price)) / candle_range,
            0
        )
        df["lower_shadow"] = np.where(
            candle_range > 0,
            (np.minimum(close, open_price) - low) / candle_range,
            0
        )

        # Doji detection (small body)
        df["is_doji"] = (np.abs(df["candle_body"]) < 0.1).astype(int)

        # Higher highs / lower lows
        df["higher_high"] = (high > high.shift(1)).astype(int)
        df["lower_low"] = (low < low.shift(1)).astype(int)

        # Distance from recent high/low
        rolling_high = high.rolling(20).max()
        rolling_low = low.rolling(20).min()
        df["dist_from_high"] = (rolling_high - close) / close
        df["dist_from_low"] = (close - rolling_low) / close

        # Support/Resistance proximity
        df["near_high"] = (df["dist_from_high"] < 0.02).astype(int)
        df["near_low"] = (df["dist_from_low"] < 0.02).astype(int)

        return df

    def _calc_streak(self, condition: pd.Series) -> pd.Series:
        """Calculate consecutive streak of True values."""
        streaks = condition.astype(int)
        cumsum = streaks.cumsum()
        reset = cumsum.where(~condition, np.nan).ffill().fillna(0)
        return cumsum - reset

    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of classification feature columns.

        Args:
            df: DataFrame with features

        Returns:
            List of feature column names
        """
        # Exclude non-feature columns
        exclude_cols = [
            "ticker", "symbol", "timeframe", "bar_ts", "timestamp",
            "open", "high", "low", "close", "volume",  # Raw OHLCV
        ]

        feature_cols = [c for c in df.columns if c not in exclude_cols]
        return feature_cols

    def select_top_features(
        self,
        feature_importance: Dict[str, float],
        top_n: int = 20
    ) -> List[str]:
        """
        Select top N most important features.

        Args:
            feature_importance: Dict of feature -> importance score
            top_n: Number of features to select

        Returns:
            List of top feature names
        """
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [f[0] for f in sorted_features[:top_n]]
