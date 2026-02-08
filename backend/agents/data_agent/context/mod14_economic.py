"""
MOD14: Economic Data Context Module

Provides economic indicators that affect market sentiment and predictions.

Output columns (prefix: econ_):
- cpi_yoy: CPI year-over-year change
- cpi_mom: CPI month-over-month change
- cpi_trend: CPI trend direction (rising, falling, stable)
- unemployment_rate: Current unemployment rate
- unemployment_trend: Unemployment trend direction
- consumer_sentiment: University of Michigan Consumer Sentiment
- fed_funds_rate: Federal Funds Rate
- economic_surprise_index: Composite surprise indicator
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class EconomicContext:
    """
    Economic data context module.

    Uses FRED API for all economic indicators.
    """

    def __init__(self):
        self._fred_collector = None
        self._cached_data: Optional[pd.DataFrame] = None
        self._cache_date: Optional[str] = None

    def _get_fred_collector(self):
        """Lazy-load FRED collector."""
        if self._fred_collector is None:
            try:
                from ..collectors import FREDCollector
                self._fred_collector = FREDCollector()
                self._fred_collector.initialize()
            except Exception as e:
                logger.warning(f"Could not initialize FRED collector: {e}")
        return self._fred_collector

    def _calculate_trend(self, series: pd.Series, periods: int = 3) -> str:
        """Calculate trend direction from a series."""
        if series is None or len(series) < periods + 1:
            return "stable"

        recent = series.iloc[-periods:]
        if recent.is_monotonic_increasing:
            return "rising"
        elif recent.is_monotonic_decreasing:
            return "falling"
        else:
            # Check overall direction
            if recent.iloc[-1] > recent.iloc[0]:
                return "rising"
            elif recent.iloc[-1] < recent.iloc[0]:
                return "falling"
            return "stable"

    def _calculate_surprise_index(
        self,
        cpi_yoy: Optional[float],
        unemployment: Optional[float],
        sentiment: Optional[float],
    ) -> float:
        """
        Calculate a simple economic surprise index.

        Positive = economy better than expected
        Negative = economy worse than expected
        """
        # This is a simplified version - in production would compare to consensus
        score = 0.0
        count = 0

        # Lower unemployment is positive
        if unemployment is not None:
            if unemployment < 4.0:
                score += 1.0
            elif unemployment < 5.0:
                score += 0.5
            elif unemployment > 6.0:
                score -= 1.0
            count += 1

        # Higher sentiment is positive
        if sentiment is not None:
            if sentiment > 80:
                score += 1.0
            elif sentiment > 70:
                score += 0.5
            elif sentiment < 60:
                score -= 0.5
            elif sentiment < 50:
                score -= 1.0
            count += 1

        # Moderate CPI is positive (not too high, not deflationary)
        if cpi_yoy is not None:
            if 1.5 <= cpi_yoy <= 2.5:
                score += 1.0
            elif 2.5 < cpi_yoy <= 3.5:
                score += 0.0
            elif cpi_yoy > 4.0:
                score -= 0.5
            elif cpi_yoy < 1.0:
                score -= 0.5
            count += 1

        return score / count if count > 0 else 0.0

    def get_context(
        self,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,  # Not used for market-wide module
    ) -> pd.DataFrame:
        """
        Get economic context for a date.

        Returns DataFrame with columns:
        - timestamp, cpi_yoy, cpi_mom, cpi_trend, unemployment_rate,
          unemployment_trend, consumer_sentiment, fed_funds_rate,
          economic_surprise_index
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        current_date = datetime.strptime(date, "%Y-%m-%d")

        # Initialize with defaults
        row = {
            "timestamp": current_date,
            "cpi_yoy": None,
            "cpi_mom": None,
            "cpi_trend": "stable",
            "unemployment_rate": None,
            "unemployment_trend": "stable",
            "consumer_sentiment": None,
            "sentiment_change_mom": None,
            "fed_funds_rate": None,
            "economic_surprise_index": 0.0,
        }

        fred = self._get_fred_collector()
        if not fred:
            logger.warning("FRED collector not available")
            return pd.DataFrame([row])

        try:
            # Fetch all economic indicators
            econ_data = fred.fetch_economic_indicators(
                current_date - timedelta(days=90),
                current_date
            )

            if econ_data is not None and not econ_data.empty:
                latest = econ_data.iloc[-1]

                row["cpi_yoy"] = latest.get("cpi_yoy")
                row["cpi_mom"] = latest.get("cpi_mom")
                row["unemployment_rate"] = latest.get("unemployment_rate")
                row["consumer_sentiment"] = latest.get("consumer_sentiment")
                row["fed_funds_rate"] = latest.get("fed_funds_rate")

                # Calculate trends
                if "cpi_yoy" in econ_data.columns:
                    row["cpi_trend"] = self._calculate_trend(econ_data["cpi_yoy"])

                if "unemployment_rate" in econ_data.columns:
                    row["unemployment_trend"] = self._calculate_trend(
                        econ_data["unemployment_rate"]
                    )

                # Calculate surprise index
                row["economic_surprise_index"] = self._calculate_surprise_index(
                    row["cpi_yoy"],
                    row["unemployment_rate"],
                    row["consumer_sentiment"],
                )

        except Exception as e:
            logger.error(f"Error fetching economic data: {e}")

        return pd.DataFrame([row])

    def get_latest_cpi(self) -> Optional[float]:
        """Get latest CPI YoY reading."""
        ctx = self.get_context()
        if ctx is not None and not ctx.empty:
            return ctx.iloc[0].get("cpi_yoy")
        return None

    def get_latest_unemployment(self) -> Optional[float]:
        """Get latest unemployment rate."""
        ctx = self.get_context()
        if ctx is not None and not ctx.empty:
            return ctx.iloc[0].get("unemployment_rate")
        return None
