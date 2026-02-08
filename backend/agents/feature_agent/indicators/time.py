"""
Time-based Features for TICK Feature Agent.

Extracted from client's modules/swing_scalp_classifier.py
"""

from datetime import datetime
from typing import Optional
import pytz
import pandas as pd


def get_session_phase(timestamp: Optional[datetime] = None) -> str:
    """
    Determine current trading session phase.
    
    Extracted from: modules/swing_scalp_classifier.py:149-177
    
    Args:
        timestamp: Datetime to check (default: current time)
        
    Returns:
        Session phase string:
        - 'pre_open': Before 9:30 AM ET
        - 'open_drive': 9:30-9:50 AM ET (first 20 mins)
        - 'morning': 9:50 AM - 11:00 AM ET
        - 'midday': 11:00 AM - 2:00 PM ET
        - 'afternoon': 2:00 PM - 3:00 PM ET
        - 'close': 3:00 PM - 4:00 PM ET (power hour)
        - 'after_hours': After 4:00 PM ET
    """
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


def get_session_minutes(timestamp: Optional[datetime] = None) -> int:
    """
    Get minutes since market open (9:30 AM ET).
    
    Reference: analysis/spx_move_discovery.py:197
    
    Args:
        timestamp: Datetime to check
        
    Returns:
        Minutes since market open (negative if pre-open)
    """
    et = pytz.timezone('US/Eastern')
    
    if timestamp is None:
        now = datetime.now(et)
    else:
        if timestamp.tzinfo is None:
            now = et.localize(timestamp)
        else:
            now = timestamp.astimezone(et)
    
    # Minutes since 9:30 AM
    session_min = (now.hour - 9) * 60 + now.minute - 30
    
    return session_min


def is_market_hours(timestamp: Optional[datetime] = None) -> bool:
    """
    Check if timestamp is during regular trading hours (9:30 AM - 4:00 PM ET).
    
    Args:
        timestamp: Datetime to check
        
    Returns:
        True if during market hours
    """
    session_min = get_session_minutes(timestamp)
    return 0 <= session_min <= 390  # 390 minutes = 6.5 hours


def get_minutes_to_close(timestamp: Optional[datetime] = None) -> int:
    """
    Get minutes until market close (4:00 PM ET).
    
    Reference: analysis/spx_move_discovery.py:198
    
    Args:
        timestamp: Datetime to check
        
    Returns:
        Minutes until close (0 or negative if after close)
    """
    session_min = get_session_minutes(timestamp)
    return max(0, 390 - session_min)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time-based features to a DataFrame with datetime index.
    
    Reference: analysis/spx_move_discovery.py:194-206
    
    Args:
        df: DataFrame with datetime index
        
    Returns:
        DataFrame with additional time columns
    """
    result = df.copy()
    
    if not isinstance(df.index, pd.DatetimeIndex):
        return result
    
    # Basic time features
    result['hour'] = df.index.hour
    result['minute'] = df.index.minute
    result['day_of_week'] = df.index.dayofweek
    
    # Session minutes
    result['session_min'] = (df.index.hour - 9) * 60 + df.index.minute - 30
    result['mins_to_close'] = 390 - result['session_min']
    
    # Session buckets (30-min intervals)
    result['session_bucket'] = (result['session_min'] // 30).astype(int)
    
    # Session flags
    result['is_open_5'] = result['session_min'] < 5
    result['is_open_15'] = result['session_min'] < 15
    result['is_open_30'] = result['session_min'] < 30
    result['is_power_hour'] = result['session_min'] >= 330
    result['is_close_15'] = result['session_min'] >= 375
    result['is_half_hour'] = result['minute'].isin([0, 30])
    
    return result




