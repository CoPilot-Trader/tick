"""
Public interfaces for the Feature Agent.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class TechnicalIndicators(BaseModel):
    """Technical indicators output."""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    ema_20: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    adx: Optional[float] = None
    atr: Optional[float] = None
    obv: Optional[float] = None
    # Add more indicators as needed


class EngineeredFeatures(BaseModel):
    """Engineered features output."""
    returns_1d: Optional[float] = None
    returns_7d: Optional[float] = None
    returns_30d: Optional[float] = None
    volatility_7d: Optional[float] = None
    volatility_30d: Optional[float] = None
    price_change_pct: Optional[float] = None
    volume_change_pct: Optional[float] = None
    # Add more features as needed


class FeatureResponse(BaseModel):
    """Response containing features and indicators."""
    symbol: str
    timestamp: datetime
    indicators: TechnicalIndicators
    features: EngineeredFeatures
    timeframe: str

