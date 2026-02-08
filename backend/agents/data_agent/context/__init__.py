"""
Context Modules for TICK Data Pipeline.

These modules enrich OHLCV data with contextual information for predictions.

Module Types:
- MARKET_WIDE: VIX, yields, economic data (MOD06, MOD09, MOD14)
- TICKER_SPECIFIC: Sentiment, earnings (MOD10, MOD13)
- SECTOR_LEVEL: Sector rotation (MOD11)
"""

from .loader import ContextLoader
from .mod06_events import EventsContext
from .mod09_macro import MacroContext
from .mod10_sentiment import SentimentContext
from .mod11_rotation import RotationContext
from .mod13_earnings import EarningsContext
from .mod14_economic import EconomicContext

__all__ = [
    "ContextLoader",
    "EventsContext",
    "MacroContext",
    "SentimentContext",
    "RotationContext",
    "EarningsContext",
    "EconomicContext",
]
