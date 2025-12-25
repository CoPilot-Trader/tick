"""
Public interfaces for the Support/Resistance Agent.
"""

from typing import List
from datetime import datetime
from pydantic import BaseModel


class PriceLevel(BaseModel):
    """Support or resistance level."""
    price: float
    strength: int  # 0-100
    type: str  # "support" or "resistance"
    touches: int  # Number of times price touched this level
    validated: bool
    first_touch: datetime
    last_touch: datetime


class SupportResistanceResponse(BaseModel):
    """Response containing support/resistance levels."""
    symbol: str
    timestamp: datetime
    support_levels: List[PriceLevel]
    resistance_levels: List[PriceLevel]
    total_levels: int

