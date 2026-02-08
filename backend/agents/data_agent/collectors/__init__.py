"""
Data Collectors for TICK Data Agent.

This module contains collectors for fetching market data from various sources.
Supports both historical (batch) and real-time data collection.

Collectors:
- YFinanceCollector: Free, good for OHLCV data (fallback)
- TiingoCollector: Primary source for EOD and IEX intraday data
- FMPCollector: Earnings calendar, economic events, company profiles
- FREDCollector: Economic indicators (VIX, yields, CPI, unemployment)
- AlphaVantageCollector: News sentiment (for MOD10)
"""

from .base import BaseCollector, CollectorResult
from .yfinance_collector import YFinanceCollector
from .alpha_vantage_collector import AlphaVantageCollector
from .tiingo_collector import TiingoCollector
from .fmp_collector import FMPCollector
from .fred_collector import FREDCollector

__all__ = [
    "BaseCollector",
    "CollectorResult",
    "YFinanceCollector",
    "AlphaVantageCollector",
    "TiingoCollector",
    "FMPCollector",
    "FREDCollector",
]




