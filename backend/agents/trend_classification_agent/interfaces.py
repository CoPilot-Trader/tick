"""
Public interfaces for the Trend Classification Agent.
"""

from datetime import datetime
from pydantic import BaseModel
from typing import Dict


class TrendClassification(BaseModel):
    """Trend classification result."""
    symbol: str
    timestamp: datetime
    timeframe: str
    signal: str  # BUY, SELL, or HOLD
    probabilities: Dict[str, float]  # {"BUY": 0.65, "SELL": 0.20, "HOLD": 0.15}
    confidence: float  # 0.0 to 1.0
    model: str  # "lightgbm" or "xgboost"

