"""
Public interfaces for the Fusion Agent.
"""

from typing import Dict
from datetime import datetime
from pydantic import BaseModel


class ComponentSignal(BaseModel):
    """Component signal contribution."""
    weight: float
    contribution: float
    signal: str  # BUY, SELL, HOLD, or NEUTRAL


class FusedSignal(BaseModel):
    """Fused trading signal."""
    symbol: str
    signal: str  # BUY, SELL, or HOLD
    confidence: float  # 0.0 to 1.0
    components: Dict[str, ComponentSignal]
    fused_at: datetime

