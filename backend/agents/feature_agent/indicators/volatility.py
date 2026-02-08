"""
Volatility Indicators for TICK Feature Agent.

Extracted from client's modules/swing_scalp_classifier.py and enhanced.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Extracted from: modules/swing_scalp_classifier.py:103-116
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default: 14)
        
    Returns:
        Series with ATR values
    """
    df = df.copy()
    
    # Previous close (fill first value with current close)
    prev_close = df['close'].shift(1)
    prev_close = prev_close.fillna(df['close'])
    
    # True Range components
    hl = df['high'] - df['low']
    hpc = (df['high'] - prev_close).abs()
    lpc = (df['low'] - prev_close).abs()
    
    # True Range is max of the three
    tr = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
    
    # ATR is rolling mean of True Range
    atr = tr.rolling(window=period, min_periods=1).mean()
    
    return atr


def calc_atr_percentile(df: pd.DataFrame, period: int = 14, lookback: int = 20) -> float:
    """
    Calculate where current ATR stands vs recent ATR readings.
    
    Extracted from: modules/swing_scalp_classifier.py:119-132
    
    Args:
        df: DataFrame with OHLC data
        period: ATR period
        lookback: Number of bars to compare against
        
    Returns:
        Percentile (0-100) of current ATR
    """
    if len(df) < period + lookback:
        return 50.0
    
    atr = calc_atr(df, period)
    current_atr = atr.iloc[-1]
    recent_atrs = atr.iloc[-lookback:].dropna()
    
    if len(recent_atrs) == 0:
        return 50.0
    
    percentile = (recent_atrs < current_atr).sum() / len(recent_atrs) * 100
    return round(percentile, 1)


def calc_bollinger_bands(
    series: pd.Series, 
    period: int = 20, 
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        series: Price series (typically close)
        period: Moving average period
        std_dev: Standard deviation multiplier
        
    Returns:
        Tuple of (middle, upper, lower) bands
    """
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return middle, upper, lower


def calc_historical_volatility(series: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Historical Volatility (annualized standard deviation of returns).
    
    Args:
        series: Price series (typically close)
        period: Lookback period
        
    Returns:
        Series with historical volatility values
    """
    # Calculate log returns
    log_returns = np.log(series / series.shift(1))
    
    # Rolling standard deviation
    rolling_std = log_returns.rolling(window=period).std()
    
    # Annualize (assuming 252 trading days)
    hist_vol = rolling_std * np.sqrt(252)
    
    return hist_vol
