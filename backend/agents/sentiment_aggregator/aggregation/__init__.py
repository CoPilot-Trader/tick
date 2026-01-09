"""
Aggregation Module Package

This package contains sentiment aggregation logic:
- Time-weighted aggregation (recent news weighted more)
- Impact scoring (High/Medium/Low based on sentiment strength, volume, recency)

Why this package exists:
- Separates aggregation logic from main agent
- Makes aggregation algorithms reusable
- Easy to test independently
- Easy to add new aggregation methods
"""

from .time_weighted import TimeWeightedAggregator
from .impact_scorer import ImpactScorer

__all__ = [
    "TimeWeightedAggregator",
    "ImpactScorer",
]

