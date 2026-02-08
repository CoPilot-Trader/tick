"""
Price-based Features for TICK Feature Agent.

Extracted from client's analysis/spx_move_discovery.py
"""

import pandas as pd
import numpy as np
from typing import Dict, List


def calc_returns(series: pd.Series, periods: List[int] = None) -> pd.DataFrame:
    """
    Calculate returns over multiple periods.
    
    Args:
        series: Price series (typically close)
        periods: List of periods (default: [1, 5, 10, 20])
        
    Returns:
        DataFrame with return columns
    """
    if periods is None:
        periods = [1, 5, 10, 20]
    
    result = pd.DataFrame(index=series.index)
    
    for period in periods:
        # Simple return
        result[f'return_{period}'] = series.pct_change(period)
        
        # Log return
        result[f'log_return_{period}'] = np.log(series / series.shift(period))
    
    return result


def calc_price_position(df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
    """
    Calculate price position within range over multiple periods.
    
    Reference: analysis/spx_move_discovery.py:142-149
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        periods: List of periods (default: [5, 10, 20, 50])
        
    Returns:
        DataFrame with position columns
    """
    if periods is None:
        periods = [5, 10, 20, 50]
    
    result = pd.DataFrame(index=df.index)
    
    for period in periods:
        high_n = df['high'].rolling(period).max()
        low_n = df['low'].rolling(period).min()
        range_n = high_n - low_n
        
        result[f'high_{period}'] = high_n
        result[f'low_{period}'] = low_n
        result[f'range_{period}'] = range_n
        result[f'pos_in_range_{period}'] = (df['close'] - low_n) / range_n.replace(0, np.nan)
    
    return result


def calc_bar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate bar-level microstructure features.
    
    Reference: analysis/spx_move_discovery.py:151-156
    
    Args:
        df: DataFrame with OHLC columns
        
    Returns:
        DataFrame with bar features
    """
    result = pd.DataFrame(index=df.index)
    
    # Bar structure
    result['bar_range'] = df['high'] - df['low']
    result['bar_body'] = (df['close'] - df['open']).abs()
    result['bar_direction'] = np.sign(df['close'] - df['open'])
    
    # Range vs average
    result['range_vs_avg'] = result['bar_range'] / result['bar_range'].rolling(10).mean()
    
    # Body percentage of range
    result['body_pct'] = result['bar_body'] / result['bar_range'].replace(0, np.nan)
    
    # Upper/Lower wick
    result['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    result['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    result['wick_ratio'] = result['upper_wick'] / result['lower_wick'].replace(0, np.nan)
    
    return result


def calc_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate momentum/velocity features.
    
    Reference: analysis/spx_move_discovery.py:158-170
    
    Args:
        df: DataFrame with 'close' column
        
    Returns:
        DataFrame with momentum features
    """
    result = pd.DataFrame(index=df.index)
    
    # Moves over different periods
    for bars in [1, 2, 3, 5]:
        result[f'move_{bars}'] = df['close'].diff(bars)
        result[f'move_{bars}_pct'] = df['close'].pct_change(bars) * 100
        result[f'velocity_{bars}'] = result[f'move_{bars}'] / bars
    
    # Acceleration
    result['accel'] = result['velocity_1'].diff(1)
    result['accel_2'] = result['velocity_1'].diff(2)
    
    # Momentum consistency
    result['momentum_consistent'] = (
        (np.sign(result['move_1']) == np.sign(result['move_2'])) &
        (np.sign(result['move_2']) == np.sign(result['move_3']))
    ).astype(int)
    
    return result


def calc_compression_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate compression/expansion features.
    
    Reference: analysis/spx_move_discovery.py:172-180
    
    Args:
        df: DataFrame with 'high', 'low' columns
        
    Returns:
        DataFrame with compression features
    """
    result = pd.DataFrame(index=df.index)
    
    # Range over different windows
    result['range_1'] = df['high'] - df['low']
    result['range_3'] = df['high'].rolling(3).max() - df['low'].rolling(3).min()
    result['range_5'] = df['high'].rolling(5).max() - df['low'].rolling(5).min()
    result['range_10'] = df['high'].rolling(10).max() - df['low'].rolling(10).min()
    
    # Compression ratios
    result['compress_1v5'] = result['range_1'] / result['range_5'].replace(0, np.nan)
    result['compress_3v10'] = result['range_3'] / result['range_10'].replace(0, np.nan)
    
    # Range contracting flag
    result['range_contracting'] = result['range_3'] < result['range_3'].shift(3) * 0.7
    
    return result


def calc_daily_context(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily context features (from open, day's range position).
    
    Reference: analysis/spx_move_discovery.py:220-228
    
    Args:
        df: DataFrame with OHLC columns and datetime index
        
    Returns:
        DataFrame with daily context features
    """
    result = pd.DataFrame(index=df.index)
    
    if not isinstance(df.index, pd.DatetimeIndex):
        return result
    
    # Daily open
    result['daily_open'] = df.groupby(df.index.date)['open'].transform('first')
    result['from_open'] = df['close'] - result['daily_open']
    result['from_open_pct'] = result['from_open'] / result['daily_open'] * 100
    
    # Day's high/low
    result['day_high'] = df.groupby(df.index.date)['high'].cummax()
    result['day_low'] = df.groupby(df.index.date)['low'].cummin()
    result['day_range'] = result['day_high'] - result['day_low']
    
    # Position in day's range
    result['pos_in_day'] = (df['close'] - result['day_low']) / result['day_range'].replace(0, np.nan)
    
    return result




