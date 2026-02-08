"""
Trend Indicators for TICK Feature Agent.

Based on patterns from client's modules/level_exhaustion.py and standard implementations.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calc_sma(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        series: Price series
        period: SMA period
        
    Returns:
        Series with SMA values
    """
    return series.rolling(window=period).mean()


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).
    
    Reference: modules/level_exhaustion.py:396-397
    
    Args:
        series: Price series
        period: EMA period
        
    Returns:
        Series with EMA values
    """
    return series.ewm(span=period, adjust=False).mean()


def calc_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (ADX).
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ADX period (default: 14)
        
    Returns:
        Series with ADX values (0-100)
    """
    # Calculate +DM and -DM
    high_diff = df['high'].diff()
    low_diff = df['low'].diff()
    
    plus_dm = high_diff.where((high_diff > low_diff.abs()) & (high_diff > 0), 0)
    minus_dm = low_diff.abs().where((low_diff.abs() > high_diff) & (low_diff < 0), 0)
    
    # Calculate True Range
    prev_close = df['close'].shift(1)
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - prev_close).abs()
    tr3 = (df['low'] - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Smoothed values (Wilder's smoothing)
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    plus_di_smooth = plus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    minus_di_smooth = minus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    # +DI and -DI
    plus_di = 100 * plus_di_smooth / atr.replace(0, np.nan)
    minus_di = 100 * minus_di_smooth / atr.replace(0, np.nan)
    
    # DX and ADX
    di_sum = plus_di + minus_di
    di_diff = (plus_di - minus_di).abs()
    dx = 100 * di_diff / di_sum.replace(0, np.nan)
    
    adx = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    return adx


def calc_plus_di(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate +DI (Positive Directional Indicator).
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: DI period (default: 14)
        
    Returns:
        Series with +DI values
    """
    high_diff = df['high'].diff()
    low_diff = df['low'].diff()
    
    plus_dm = high_diff.where((high_diff > low_diff.abs()) & (high_diff > 0), 0)
    
    # True Range
    prev_close = df['close'].shift(1)
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - prev_close).abs()
    tr3 = (df['low'] - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Smoothed
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    plus_di_smooth = plus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    plus_di = 100 * plus_di_smooth / atr.replace(0, np.nan)
    
    return plus_di


def calc_minus_di(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate -DI (Negative Directional Indicator).
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: DI period (default: 14)
        
    Returns:
        Series with -DI values
    """
    high_diff = df['high'].diff()
    low_diff = df['low'].diff()
    
    minus_dm = low_diff.abs().where((low_diff.abs() > high_diff) & (low_diff < 0), 0)
    
    # True Range
    prev_close = df['close'].shift(1)
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - prev_close).abs()
    tr3 = (df['low'] - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Smoothed
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    minus_di_smooth = minus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    minus_di = 100 * minus_di_smooth / atr.replace(0, np.nan)
    
    return minus_di


# Standard MA configurations from client's code
# Reference: modules/level_exhaustion.py:374-383
MA_CONFIGS = {
    '5m': [('ema_20', 20, 'ema')],
    '10m': [('ema_20', 20, 'ema')],
    '1h': [('ema_20', 20, 'ema'), ('sma_50', 50, 'sma')],
    '60m': [('ema_20', 20, 'ema'), ('sma_50', 50, 'sma')],
    '1d': [
        ('ema_9', 9, 'ema'),
        ('ema_20', 20, 'ema'),
        ('sma_50', 50, 'sma'),
        ('sma_200', 200, 'sma')
    ],
    'daily': [
        ('ema_9', 9, 'ema'),
        ('ema_20', 20, 'ema'),
        ('sma_50', 50, 'sma'),
        ('sma_200', 200, 'sma')
    ],
}


def calc_all_mas(df: pd.DataFrame, timeframe: str = 'daily') -> pd.DataFrame:
    """
    Calculate all moving averages for a given timeframe.
    
    Reference: modules/level_exhaustion.py:366-410
    
    Args:
        df: DataFrame with 'close' column
        timeframe: Timeframe key from MA_CONFIGS
        
    Returns:
        DataFrame with MA columns added
    """
    result = df.copy()
    configs = MA_CONFIGS.get(timeframe, MA_CONFIGS['daily'])
    
    for name, period, ma_type in configs:
        if len(df) < period:
            result[name] = np.nan
            continue
        
        if ma_type == 'ema':
            result[name] = calc_ema(df['close'], period)
        else:
            result[name] = calc_sma(df['close'], period)
    
    return result
