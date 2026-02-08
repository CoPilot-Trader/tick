"""
Volume Indicators for TICK Feature Agent.

Extracted from client's modules/swing_scalp_classifier.py and signals/volume.py
"""

import pandas as pd
import numpy as np
from typing import Optional


def calc_volume_ratio(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    """
    Calculate current volume vs average volume ratio.
    
    Extracted from: modules/swing_scalp_classifier.py:135-146
    
    Args:
        df: DataFrame with 'volume' column
        lookback: Number of bars for average calculation
        
    Returns:
        Series with volume ratio (1.0 = average)
    """
    if 'volume' not in df.columns:
        return pd.Series(index=df.index, data=1.0)
    
    avg_vol = df['volume'].rolling(window=lookback, min_periods=3).mean()
    ratio = df['volume'] / avg_vol.replace(0, np.nan)
    
    return ratio.round(2)


def calc_relative_volume(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    """
    Calculate relative volume (volume / SMA of volume).
    
    Extracted from: signals/volume.py:25
    
    Args:
        df: DataFrame with 'volume' column
        lookback: Lookback period
        
    Returns:
        Series with relative volume values
    """
    v = df['volume'].fillna(0)
    rvol = v / v.rolling(lookback, min_periods=max(3, lookback // 3)).mean()
    return rvol


def calc_volume_acceleration(df: pd.DataFrame, ema_span: int = 5) -> pd.Series:
    """
    Calculate volume acceleration (first diff of EMA of volume).
    
    Extracted from: signals/volume.py:26-27
    
    Args:
        df: DataFrame with 'volume' column
        ema_span: EMA period for smoothing
        
    Returns:
        Series with volume acceleration
    """
    v = df['volume'].fillna(0)
    vol_ema = v.ewm(span=ema_span, adjust=False).mean()
    return vol_ema.diff()


def calc_volume_ma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Calculate Volume Moving Average.
    
    Args:
        df: DataFrame with 'volume' column
        period: MA period
        
    Returns:
        Series with volume MA
    """
    return df['volume'].rolling(window=period).mean()


def calc_obv(df: pd.DataFrame) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).
    
    Args:
        df: DataFrame with 'close' and 'volume' columns
        
    Returns:
        Series with OBV values
    """
    # Direction based on close change
    direction = np.sign(df['close'].diff())
    
    # OBV is cumulative sum of signed volume
    obv = (direction * df['volume']).cumsum()
    
    return obv


def calc_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume-Weighted Average Price (VWAP).
    
    Extracted from: analysis/spx_move_discovery.py:208-213
    
    Note: For intraday data, VWAP resets each day.
    For daily data, VWAP is just the typical price.
    
    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns
              Should have datetime index for intraday reset
        
    Returns:
        Series with VWAP values
    """
    # Typical Price
    typical = (df['high'] + df['low'] + df['close']) / 3
    
    # Volume * Typical Price
    vol_price = typical * df['volume']
    
    # Check if we have datetime index for intraday reset
    if isinstance(df.index, pd.DatetimeIndex):
        # Group by date and calculate cumulative VWAP
        vwap = vol_price.groupby(df.index.date).cumsum() / \
               df['volume'].groupby(df.index.date).cumsum()
    else:
        # No date index - just cumulative
        vwap = vol_price.cumsum() / df['volume'].cumsum()
    
    return vwap


def tag_reversal_with_accel(
    df: pd.DataFrame,
    rvol_lb: int = 20,
    rvol_min: float = 1.5,
    vol_ema_span: int = 5
) -> pd.DataFrame:
    """
    Tag reversal points with volume acceleration.
    
    Extracted from: signals/volume.py:8-47
    
    Adds columns:
      - VOL_RVOL: Relative volume
      - VOL_ACCEL: Volume acceleration
      - PIVOT_LOW/HIGH: 3-bar pivot points
      - REVERSAL_ACCEL_BULL/BEAR: Reversal signals
      - REVERSAL_ACCEL_SCORE: Confidence score
    
    Args:
        df: DataFrame with OHLCV columns
        rvol_lb: Relative volume lookback
        rvol_min: Minimum relative volume for signal
        vol_ema_span: Volume EMA span for acceleration
        
    Returns:
        DataFrame with additional columns
    """
    out = df.copy()
    
    # Defensive fills
    v = out['volume'].fillna(0)
    
    # Relative volume and acceleration
    out['VOL_RVOL'] = v / v.rolling(rvol_lb, min_periods=max(3, rvol_lb // 3)).mean()
    vol_ema_fast = v.ewm(span=vol_ema_span, adjust=False).mean()
    out['VOL_ACCEL'] = vol_ema_fast.diff()
    
    # 3-bar pivots
    out['PIVOT_LOW'] = (out['low'] < out['low'].shift(1)) & (out['low'] < out['low'].shift(-1))
    out['PIVOT_HIGH'] = (out['high'] > out['high'].shift(1)) & (out['high'] > out['high'].shift(-1))
    
    # Reversal + acceleration criteria
    rvol_ok = out['VOL_RVOL'] >= rvol_min
    accel_up = out['VOL_ACCEL'] > 0
    green = out['close'] > out['open']
    red = out['close'] < out['open']
    
    out['REVERSAL_ACCEL_BULL'] = out['PIVOT_LOW'] & green & rvol_ok & accel_up
    out['REVERSAL_ACCEL_BEAR'] = out['PIVOT_HIGH'] & red & rvol_ok & accel_up
    out['REVERSAL_ACCEL'] = out['REVERSAL_ACCEL_BULL'] | out['REVERSAL_ACCEL_BEAR']
    
    # Confidence score: RVOL × normalized accel
    denom = v.rolling(rvol_lb, min_periods=max(3, rvol_lb // 3)).mean().replace(0, np.nan)
    out['REVERSAL_ACCEL_SCORE'] = out['VOL_RVOL'] * (out['VOL_ACCEL'] / denom).clip(lower=0).fillna(0)
    
    return out
