"""
Public interfaces for the News Agent.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class NewsArticle(BaseModel):
    """News article model."""
    id: str
    title: str
    source: str
    published_at: datetime
    relevance_score: float
    sentiment: str  # positive, neutral, negative
    summary: Optional[str] = None
    url: Optional[str] = None


class SentimentData(BaseModel):
    """Sentiment analysis result."""
    symbol: str
    timestamp: datetime
    sentiment_score: float  # -1.0 to 1.0
    sentiment_label: str  # positive, neutral, negative
    confidence: float  # 0.0 to 1.0
    news_count: int


class NewsResponse(BaseModel):
    """Response containing filtered news articles."""
    articles: List[NewsArticle]
    symbol: str
    filtered_at: datetime

