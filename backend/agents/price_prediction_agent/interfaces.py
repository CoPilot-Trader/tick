"""
Public interfaces for the Price Prediction Agent.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class PricePrediction(BaseModel):
    """Price prediction for a specific horizon."""
    horizon: str  # e.g., "1d", "7d", "30d"
    predicted_price: float
    confidence: float  # 0.0 to 1.0
    upper_bound: float
    lower_bound: float


class TechnicalIndicators(BaseModel):
    """Technical indicators for a symbol."""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    moving_average_50: Optional[float] = None
    moving_average_200: Optional[float] = None
    # Add more indicators as needed


class PredictionResponse(BaseModel):
    """Response containing price predictions."""
    symbol: str
    current_price: float
    predictions: List[PricePrediction]
    technical_indicators: TechnicalIndicators
    predicted_at: datetime

