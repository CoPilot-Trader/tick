"""
Public interfaces for the LLM Sentiment Agent.
"""

from datetime import datetime
from pydantic import BaseModel


class SentimentScore(BaseModel):
    """Sentiment analysis result."""
    symbol: str
    article_id: str
    sentiment_score: float  # -1.0 to +1.0
    sentiment_label: str  # positive, neutral, negative
    confidence: float  # 0.0 to 1.0
    processed_at: datetime
    cached: bool  # Whether result was from cache

