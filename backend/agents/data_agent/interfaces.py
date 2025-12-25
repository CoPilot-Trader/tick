"""
Public interfaces for the Data Agent.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class OHLCVDataPoint(BaseModel):
    """Single OHLCV data point."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoricalDataResponse(BaseModel):
    """Response containing historical OHLCV data."""
    symbol: str
    data: List[OHLCVDataPoint]
    timeframe: str
    start_date: datetime
    end_date: datetime
    total_points: int


class RealtimeDataResponse(BaseModel):
    """Response containing real-time OHLCV data."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str


class DataQualityReport(BaseModel):
    """Data quality validation report."""
    symbol: str
    accuracy: float  # 0.0 to 1.0
    completeness: float  # 0.0 to 1.0
    outliers_count: int
    missing_periods: List[str]
    validation_timestamp: datetime

