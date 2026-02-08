"""
Data Preparation Utilities for Price Forecast Agent.

Provides:
- Data cleaning and validation
- Feature engineering for forecasting
- Data transformation utilities
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataPrep:
    """
    Data preparation utilities for price forecasting.

    Features:
    - Data cleaning and validation
    - Missing value handling
    - Feature engineering
    - Data normalization
    """

    # Required columns for forecasting
    REQUIRED_COLUMNS = ["close"]
    OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

    @staticmethod
    def validate_data(
        df: pd.DataFrame,
        min_rows: int = 60,
        required_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate DataFrame for forecasting.

        Args:
            df: Input DataFrame
            min_rows: Minimum required rows
            required_columns: Required column names

        Returns:
            Validation result with issues list
        """
        issues = []
        required = required_columns or DataPrep.REQUIRED_COLUMNS

        # Check minimum rows
        if len(df) < min_rows:
            issues.append(f"Insufficient data: {len(df)} rows (need >= {min_rows})")

        # Check required columns
        missing_cols = [c for c in required if c not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")

        # Check for NaN values in required columns
        if not missing_cols:
            nan_counts = df[required].isna().sum()
            cols_with_nan = nan_counts[nan_counts > 0].to_dict()
            if cols_with_nan:
                issues.append(f"NaN values found: {cols_with_nan}")

        # Check for duplicate timestamps
        timestamp_col = None
        for col in ["bar_ts", "timestamp"]:
            if col in df.columns:
                timestamp_col = col
                break

        if timestamp_col:
            duplicates = df[timestamp_col].duplicated().sum()
            if duplicates > 0:
                issues.append(f"Duplicate timestamps: {duplicates}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "row_count": len(df),
            "columns": list(df.columns),
        }

    @staticmethod
    def clean_data(
        df: pd.DataFrame,
        fill_method: str = "ffill",
        drop_na: bool = True
    ) -> pd.DataFrame:
        """
        Clean DataFrame for forecasting.

        Args:
            df: Input DataFrame
            fill_method: Method for filling NaN ("ffill", "bfill", "interpolate")
            drop_na: Drop remaining NaN rows

        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()

        # Handle missing values
        if fill_method == "ffill":
            df_clean = df_clean.ffill()
        elif fill_method == "bfill":
            df_clean = df_clean.bfill()
        elif fill_method == "interpolate":
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            df_clean[numeric_cols] = df_clean[numeric_cols].interpolate()

        # Drop any remaining NaN
        if drop_na:
            df_clean = df_clean.dropna()

        # Remove duplicates if timestamp column exists
        timestamp_col = None
        for col in ["bar_ts", "timestamp"]:
            if col in df_clean.columns:
                timestamp_col = col
                break

        if timestamp_col:
            df_clean = df_clean.drop_duplicates(subset=[timestamp_col], keep="last")

        # Sort by timestamp
        if timestamp_col:
            df_clean = df_clean.sort_values(timestamp_col).reset_index(drop=True)

        return df_clean

    @staticmethod
    def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add time-based features for forecasting.

        Args:
            df: DataFrame with timestamp column

        Returns:
            DataFrame with time features
        """
        df_feat = df.copy()

        # Get timestamp column
        timestamp_col = None
        for col in ["bar_ts", "timestamp"]:
            if col in df_feat.columns:
                timestamp_col = col
                break

        if timestamp_col is None:
            return df_feat

        timestamps = pd.to_datetime(df_feat[timestamp_col])

        # Time features
        df_feat["day_of_week"] = timestamps.dt.dayofweek
        df_feat["day_of_month"] = timestamps.dt.day
        df_feat["month"] = timestamps.dt.month
        df_feat["quarter"] = timestamps.dt.quarter

        # Cyclical encoding (for neural networks)
        df_feat["day_sin"] = np.sin(2 * np.pi * timestamps.dt.dayofweek / 7)
        df_feat["day_cos"] = np.cos(2 * np.pi * timestamps.dt.dayofweek / 7)
        df_feat["month_sin"] = np.sin(2 * np.pi * timestamps.dt.month / 12)
        df_feat["month_cos"] = np.cos(2 * np.pi * timestamps.dt.month / 12)

        return df_feat

    @staticmethod
    def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add price-based features for forecasting.

        Args:
            df: DataFrame with OHLCV columns

        Returns:
            DataFrame with price features
        """
        df_feat = df.copy()

        if "close" not in df_feat.columns:
            return df_feat

        close = df_feat["close"]

        # Returns
        df_feat["returns_1d"] = close.pct_change(1)
        df_feat["returns_5d"] = close.pct_change(5)
        df_feat["returns_20d"] = close.pct_change(20)

        # Log returns
        df_feat["log_returns"] = np.log(close / close.shift(1))

        # Momentum
        df_feat["momentum_5d"] = close / close.shift(5) - 1
        df_feat["momentum_20d"] = close / close.shift(20) - 1

        # Volatility (rolling std of returns)
        df_feat["volatility_5d"] = df_feat["returns_1d"].rolling(5).std()
        df_feat["volatility_20d"] = df_feat["returns_1d"].rolling(20).std()

        # Price ranges
        if all(c in df_feat.columns for c in ["high", "low"]):
            df_feat["daily_range"] = df_feat["high"] - df_feat["low"]
            df_feat["daily_range_pct"] = df_feat["daily_range"] / close

        # Price position within range
        if all(c in df_feat.columns for c in ["high", "low"]):
            hl_range = df_feat["high"] - df_feat["low"]
            df_feat["close_position"] = np.where(
                hl_range > 0,
                (close - df_feat["low"]) / hl_range,
                0.5
            )

        # Moving averages ratios
        df_feat["price_sma_5_ratio"] = close / close.rolling(5).mean()
        df_feat["price_sma_20_ratio"] = close / close.rolling(20).mean()

        return df_feat

    @staticmethod
    def add_lagged_features(
        df: pd.DataFrame,
        columns: List[str],
        lags: List[int] = [1, 2, 3, 5, 10]
    ) -> pd.DataFrame:
        """
        Add lagged features.

        Args:
            df: Input DataFrame
            columns: Columns to lag
            lags: Lag periods to create

        Returns:
            DataFrame with lagged features
        """
        df_feat = df.copy()

        for col in columns:
            if col not in df_feat.columns:
                continue

            for lag in lags:
                df_feat[f"{col}_lag_{lag}"] = df_feat[col].shift(lag)

        return df_feat

    @staticmethod
    def prepare_for_training(
        df: pd.DataFrame,
        add_features: bool = True,
        min_rows: int = 60
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Full data preparation pipeline for training.

        Args:
            df: Raw input DataFrame
            add_features: Add engineered features
            min_rows: Minimum required rows

        Returns:
            Prepared DataFrame and preparation info
        """
        info = {
            "original_rows": len(df),
            "features_added": [],
        }

        # Validate
        validation = DataPrep.validate_data(df, min_rows=min_rows)
        if not validation["valid"]:
            logger.warning(f"Validation issues: {validation['issues']}")

        # Clean
        df_prep = DataPrep.clean_data(df)
        info["after_cleaning_rows"] = len(df_prep)

        # Add features
        if add_features:
            df_prep = DataPrep.add_price_features(df_prep)
            info["features_added"].extend([
                "returns", "momentum", "volatility", "ranges"
            ])

            df_prep = DataPrep.add_time_features(df_prep)
            info["features_added"].extend([
                "time_cyclical"
            ])

        # Final clean
        df_prep = df_prep.dropna()
        info["final_rows"] = len(df_prep)
        info["columns"] = list(df_prep.columns)

        return df_prep, info

    @staticmethod
    def resample_to_frequency(
        df: pd.DataFrame,
        frequency: str = "1D"
    ) -> pd.DataFrame:
        """
        Resample data to specified frequency.

        Args:
            df: Input DataFrame with timestamp
            frequency: Target frequency ("1H", "4H", "1D", "1W")

        Returns:
            Resampled DataFrame
        """
        # Get timestamp column
        timestamp_col = None
        for col in ["bar_ts", "timestamp"]:
            if col in df.columns:
                timestamp_col = col
                break

        if timestamp_col is None:
            return df

        df_resample = df.copy()
        df_resample = df_resample.set_index(pd.to_datetime(df_resample[timestamp_col]))

        # OHLCV aggregation rules
        agg_rules = {}
        if "open" in df.columns:
            agg_rules["open"] = "first"
        if "high" in df.columns:
            agg_rules["high"] = "max"
        if "low" in df.columns:
            agg_rules["low"] = "min"
        if "close" in df.columns:
            agg_rules["close"] = "last"
        if "volume" in df.columns:
            agg_rules["volume"] = "sum"

        # Resample
        df_resampled = df_resample.resample(frequency).agg(agg_rules)
        df_resampled = df_resampled.dropna()
        df_resampled = df_resampled.reset_index()
        df_resampled = df_resampled.rename(columns={"index": timestamp_col})

        return df_resampled
