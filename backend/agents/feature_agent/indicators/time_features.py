"""
Time-Based Features

Contains:
- Session Phase Detection - EXTRACTED from client's modules/swing_scalp_classifier.py
- Market Hours Filtering
- Time-of-Day Features
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Optional

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False


def get_session_phase(timestamp: Optional[datetime] = None) -> str:
    """
    Determine current trading session phase.
    
    EXTRACTED FROM: client repo modules/swing_scalp_classifier.py:149-177
    
    Args:
        timestamp: Optional datetime. Uses current time if not provided.
        
    Returns:
        Session phase string: 'pre_open', 'open_drive', 'morning', 
        'midday', 'afternoon', 'close', or 'after_hours'
    """
    if not PYTZ_AVAILABLE:
        # Fallback without timezone support
        if timestamp is None:
            timestamp = datetime.now()
        hour, minute = timestamp.hour, timestamp.minute
    else:
        et = pytz.timezone('US/Eastern')
        
        if timestamp is None:
            now = datetime.now(et)
        else:
            if timestamp.tzinfo is None:
                now = et.localize(timestamp)
            else:
                now = timestamp.astimezone(et)
        
        hour, minute = now.hour, now.minute
    
    time_decimal = hour + minute / 60
    
    if time_decimal < 9.5:
        return "pre_open"
    elif time_decimal < 9.833:  # 9:50 AM
        return "open_drive"
    elif time_decimal < 11:
        return "morning"
    elif time_decimal < 14:
        return "midday"
    elif time_decimal < 15:
        return "afternoon"
    elif time_decimal < 16:
        return "close"
    else:
        return "after_hours"


def get_market_hours_mask(df: pd.DataFrame) -> pd.Series:
    """
    Create boolean mask for regular market hours (9:30 AM - 4:00 PM ET).
    
    Args:
        df: DataFrame with DatetimeIndex
        
    Returns:
        Boolean Series (True = within market hours)
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return pd.Series(True, index=df.index)
    
    if PYTZ_AVAILABLE:
        et = pytz.timezone('US/Eastern')
        idx = df.index.tz_convert(et) if df.index.tz else df.index
    else:
        idx = df.index
    
    hour = idx.hour
    minute = idx.minute
    
    time_decimal = hour + minute / 60
    
    # Market hours: 9:30 AM (9.5) to 4:00 PM (16.0)
    return (time_decimal >= 9.5) & (time_decimal < 16)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time-based features to DataFrame.
    
    REFERENCED FROM: client repo analysis/spx_move_discovery.py:194-206
    
    Args:
        df: DataFrame with DatetimeIndex
        
    Returns:
        DataFrame with added time feature columns
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return df
    
    out = df.copy()
    
    # Basic time components
    out['hour'] = df.index.hour
    out['minute'] = df.index.minute
    out['day_of_week'] = df.index.dayofweek
    
    # Session minute (minutes since 9:30 AM)
    out['session_min'] = (df.index.hour - 9) * 60 + df.index.minute - 30
    
    # Minutes to close (4:00 PM = 390 minutes from open)
    out['mins_to_close'] = 390 - out['session_min']
    
    # Session bucket (30-minute intervals)
    out['session_bucket'] = (out['session_min'] // 30).astype(int)
    
    # Key session markers
    out['is_open_5'] = out['session_min'] < 5
    out['is_open_15'] = out['session_min'] < 15
    out['is_open_30'] = out['session_min'] < 30
    out['is_power_hour'] = out['session_min'] >= 330
    out['is_close_15'] = out['session_min'] >= 375
    out['is_half_hour'] = df.index.minute.isin([0, 30])
    
    # Market hours mask
    out['is_market_hours'] = get_market_hours_mask(df)
    
    return out


def get_session_phase_series(df: pd.DataFrame) -> pd.Series:
    """
    Get session phase for each row in DataFrame.
    
    Args:
        df: DataFrame with DatetimeIndex
        
    Returns:
        Series with session phase labels
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return pd.Series("unknown", index=df.index)
    
    return pd.Series(
        [get_session_phase(ts) for ts in df.index],
        index=df.index
    )


def get_hours_until_close(timestamp: Optional[datetime] = None) -> float:
    """
    Calculate hours remaining until market close (4pm ET).
    
    Args:
        timestamp: Optional datetime. Uses current time if not provided.
        
    Returns:
        Hours until close (0 if market is closed)
    """
    if not PYTZ_AVAILABLE:
        if timestamp is None:
            timestamp = datetime.now()
        close_hour = 16
        current_hour = timestamp.hour + timestamp.minute / 60
        return max(0, close_hour - current_hour)
    
    et = pytz.timezone('US/Eastern')
    
    if timestamp is None:
        now = datetime.now(et)
    else:
        if timestamp.tzinfo is None:
            now = et.localize(timestamp)
        else:
            now = timestamp.astimezone(et)
    
    close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if now >= close_time:
        return 0.0
    
    delta = close_time - now
    return round(delta.total_seconds() / 3600, 2)

