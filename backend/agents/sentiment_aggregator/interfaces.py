"""
Public interfaces for the Sentiment Aggregator.
"""

from datetime import datetime
from pydantic import BaseModel


class AggregatedSentiment(BaseModel):
    """Aggregated sentiment result."""
    symbol: str
    aggregated_sentiment: float  # -1.0 to +1.0
    sentiment_label: str  # positive, neutral, negative
    confidence: float  # 0.0 to 1.0
    impact: str  # High, Medium, Low
    news_count: int
    time_weighted: bool
    aggregated_at: datetime

