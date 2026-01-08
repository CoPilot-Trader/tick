"""
Utility Functions Package

This package contains utility functions used across the News Fetch Agent:
- Data normalization (convert different API formats to standard format)
- Sector mapping (map ticker symbols to sectors)
- Date range calculation (for time horizons)

Why this package exists:
- Shared utilities used by multiple modules
- Keeps agent code clean and focused
- Reusable across collectors and filters
"""

from .data_normalizer import DataNormalizer
from .sector_mapper import SectorMapper
from .date_range_calculator import DateRangeCalculator

from .logger import get_logger
from .retry import retry_with_backoff, retry_api_request

__all__ = [
    "DataNormalizer",
    "SectorMapper",
    "DateRangeCalculator",
    "get_logger",
    "retry_with_backoff",
    "retry_api_request",
]

