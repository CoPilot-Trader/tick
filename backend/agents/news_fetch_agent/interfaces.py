"""
Public interfaces for the News Fetch Agent.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class NewsArticle(BaseModel):
    """News article model."""
    id: str
    title: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    relevance_score: float  # 0.0 to 1.0


class NewsResponse(BaseModel):
    """Response containing news articles."""
    symbol: str
    articles: List[NewsArticle]
    fetched_at: datetime
    total_count: int
    sources: List[str]

