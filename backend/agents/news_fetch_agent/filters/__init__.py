"""
News Filters Package

This package contains filtering logic for news articles:
- Relevance scoring (how relevant is article to ticker)
- Duplicate detection (remove same article from multiple sources)

Why this package exists:
- Separates filtering logic from main agent
- Makes filtering logic reusable
- Easy to test independently
- Easy to add new filters (e.g., spam filter, quality filter)
"""

from .relevance_filter import RelevanceFilter
from .duplicate_filter import DuplicateFilter

__all__ = [
    "RelevanceFilter",
    "DuplicateFilter",
]

