"""
Momentum Indicators for TICK Feature Agent.

Extracted from client's modules/level_exhaustion.py and enhanced.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Extracted from: modules/level_exhaustion.py:747-759
    
    Args:
        series: Price series (typically close)
        period: RSI period (default: 14)
        
    Returns:
        Series with RSI values (0-100)
    """
    if len(series) < period + 1:
        return pd.Series(index=series.index, dtype=float)
    
    delta = series.diff()
    
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Avoid division by zero
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calc_macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        series: Price series (typically close)
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    # Calculate EMAs
    ema_fast = series.ewm(span=fast_period, adjust=False).mean()
    ema_slow = series.ewm(span=slow_period, adjust=False).mean()
    
    # MACD Line
    macd_line = ema_fast - ema_slow
    
    # Signal Line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calc_stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator (%K and %D).
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        k_period: %K period (default: 14)
        d_period: %D smoothing period (default: 3)
        
    Returns:
        Tuple of (%K, %D)
    """
    # Lowest low and highest high over period
    lowest_low = df['low'].rolling(window=k_period).min()
    highest_high = df['high'].rolling(window=k_period).max()
    
    # %K
    range_hl = highest_high - lowest_low
    k = 100 * (df['close'] - lowest_low) / range_hl.replace(0, np.nan)
    
    # %D (SMA of %K)
    d = k.rolling(window=d_period).mean()
    
    return k, d


def calc_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Calculate Commodity Channel Index (CCI).
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: CCI period (default: 20)
        
    Returns:
        Series with CCI values
    """
    # Typical Price
    tp = (df['high'] + df['low'] + df['close']) / 3
    
    # SMA of Typical Price
    sma_tp = tp.rolling(window=period).mean()
    
    # Mean Deviation
    mean_dev = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    
    # CCI
    cci = (tp - sma_tp) / (0.015 * mean_dev)
    
    return cci


def calc_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Williams %R.
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: Period (default: 14)
        
    Returns:
        Series with Williams %R values (-100 to 0)
    """
    highest_high = df['high'].rolling(window=period).max()
    lowest_low = df['low'].rolling(window=period).min()
    
    range_hl = highest_high - lowest_low
    williams_r = -100 * (highest_high - df['close']) / range_hl.replace(0, np.nan)
    
    return williams_r


def calc_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Money Flow Index (MFI).
    
    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns
        period: MFI period (default: 14)
        
    Returns:
        Series with MFI values (0-100)
    """
    # Typical Price
    tp = (df['high'] + df['low'] + df['close']) / 3
    
    # Raw Money Flow
    raw_mf = tp * df['volume']
    
    # Money Flow Direction
    tp_diff = tp.diff()
    
    # Positive and Negative Money Flow
    positive_mf = raw_mf.where(tp_diff > 0, 0)
    negative_mf = raw_mf.where(tp_diff < 0, 0)
    
    # Rolling sums
    positive_sum = positive_mf.rolling(window=period).sum()
    negative_sum = negative_mf.rolling(window=period).sum()
    
    # Money Flow Ratio
    mfr = positive_sum / negative_sum.replace(0, np.nan)
    
    # MFI
    mfi = 100 - (100 / (1 + mfr))
    
    return mfi
