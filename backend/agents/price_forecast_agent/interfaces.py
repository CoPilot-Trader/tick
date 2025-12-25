"""
Public interfaces for the Price Forecast Agent.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class PriceForecast(BaseModel):
    """Price forecast for a specific horizon."""
    horizon: str  # 1h, 4h, 1d, 1w
    predicted_price: float
    confidence: float  # 0.0 to 1.0
    upper_bound: float
    lower_bound: float
    model: str  # "prophet" or "lstm"


class ForecastResponse(BaseModel):
    """Response containing price forecasts."""
    symbol: str
    current_price: float
    predictions: List[PriceForecast]
    predicted_at: datetime

