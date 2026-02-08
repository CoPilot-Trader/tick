"""
MOD06: Events Calendar Context Module

Provides context about upcoming economic events (FOMC, CPI, Jobs, GDP).
Used to adjust predictions around high-impact events.

Output columns (prefix: evt_):
- days_to_fomc: Days until next FOMC meeting
- days_to_cpi: Days until next CPI release
- days_to_jobs: Days until next jobs report
- days_to_gdp: Days until next GDP release
- event_proximity_score: Composite score (0-1) of event nearness
- is_fomc_week: Boolean flag for FOMC week
- is_cpi_week: Boolean flag for CPI week
- next_event_type: Type of next major event
- next_event_date: Date of next major event
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class EventsContext:
    """
    Economic events calendar context module.

    Uses FMP economic calendar API for event dates.
    """

    # Known 2025/2026 FOMC meeting dates (Fed releases these in advance)
    FOMC_DATES_2025 = [
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
        "2025-07-30", "2025-09-17", "2025-11-05", "2025-12-17",
    ]

    FOMC_DATES_2026 = [
        "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16",
    ]

    # CPI is typically released around 13th of each month
    # Jobs report (NFP) is typically first Friday of each month

    def __init__(self):
        self._fmp_collector = None
        self._cached_events: Optional[pd.DataFrame] = None
        self._cache_date: Optional[str] = None

    def _get_fmp_collector(self):
        """Lazy-load FMP collector."""
        if self._fmp_collector is None:
            try:
                from ..collectors import FMPCollector
                self._fmp_collector = FMPCollector()
                self._fmp_collector.initialize()
            except Exception as e:
                logger.warning(f"Could not initialize FMP collector: {e}")
        return self._fmp_collector

    def _get_fomc_dates(self) -> List[datetime]:
        """Get all known FOMC dates."""
        dates = []
        for d in self.FOMC_DATES_2025 + self.FOMC_DATES_2026:
            dates.append(datetime.strptime(d, "%Y-%m-%d"))
        return sorted(dates)

    def _generate_cpi_dates(self, year: int) -> List[datetime]:
        """Generate approximate CPI release dates (around 13th of each month)."""
        dates = []
        for month in range(1, 13):
            # CPI is usually released on a weekday around the 13th
            target = datetime(year, month, 13)
            # Adjust if weekend
            while target.weekday() >= 5:
                target += timedelta(days=1)
            dates.append(target)
        return dates

    def _generate_jobs_dates(self, year: int) -> List[datetime]:
        """Generate Jobs Report dates (first Friday of each month)."""
        dates = []
        for month in range(1, 13):
            first_day = datetime(year, month, 1)
            # Find first Friday
            days_until_friday = (4 - first_day.weekday()) % 7
            first_friday = first_day + timedelta(days=days_until_friday)
            dates.append(first_friday)
        return dates

    def _days_to_event(self, current_date: datetime, event_dates: List[datetime]) -> int:
        """Calculate days until next event."""
        future_events = [d for d in event_dates if d >= current_date]
        if future_events:
            return (min(future_events) - current_date).days
        return 999  # No upcoming event

    def get_context(
        self,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,  # Not used for this module
    ) -> pd.DataFrame:
        """
        Get events context for a date range.

        Returns DataFrame with columns:
        - timestamp, days_to_fomc, days_to_cpi, days_to_jobs,
          event_proximity_score, is_fomc_week, is_cpi_week,
          next_event_type, next_event_date
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        current_date = datetime.strptime(date, "%Y-%m-%d")
        year = current_date.year

        # Get event dates
        fomc_dates = self._get_fomc_dates()
        cpi_dates = self._generate_cpi_dates(year) + self._generate_cpi_dates(year + 1)
        jobs_dates = self._generate_jobs_dates(year) + self._generate_jobs_dates(year + 1)

        # Generate context for a range of dates (for historical pipeline)
        # For simplicity, generate for single date here
        rows = []

        # Calculate days to each event
        days_to_fomc = self._days_to_event(current_date, fomc_dates)
        days_to_cpi = self._days_to_event(current_date, cpi_dates)
        days_to_jobs = self._days_to_event(current_date, jobs_dates)

        # Determine next event
        events = [
            ("FOMC", days_to_fomc),
            ("CPI", days_to_cpi),
            ("JOBS", days_to_jobs),
        ]
        next_event = min(events, key=lambda x: x[1])

        # Calculate proximity score (higher when closer to event)
        # Score of 1.0 when event is today, decreasing as days increase
        proximity_scores = []
        for _, days in events:
            if days <= 0:
                proximity_scores.append(1.0)
            elif days <= 3:
                proximity_scores.append(0.8)
            elif days <= 7:
                proximity_scores.append(0.5)
            elif days <= 14:
                proximity_scores.append(0.3)
            else:
                proximity_scores.append(0.1)

        event_proximity_score = max(proximity_scores)

        # Calculate next event date
        if next_event[0] == "FOMC":
            future_fomc = [d for d in fomc_dates if d >= current_date]
            next_event_date = min(future_fomc) if future_fomc else None
        elif next_event[0] == "CPI":
            future_cpi = [d for d in cpi_dates if d >= current_date]
            next_event_date = min(future_cpi) if future_cpi else None
        else:
            future_jobs = [d for d in jobs_dates if d >= current_date]
            next_event_date = min(future_jobs) if future_jobs else None

        row = {
            "timestamp": current_date,
            "days_to_fomc": days_to_fomc,
            "days_to_cpi": days_to_cpi,
            "days_to_jobs": days_to_jobs,
            "days_to_gdp": 999,  # GDP is quarterly, less frequent
            "event_proximity_score": event_proximity_score,
            "is_fomc_week": days_to_fomc <= 7,
            "is_cpi_week": days_to_cpi <= 7,
            "next_event_type": next_event[0],
            "next_event_date": next_event_date.strftime("%Y-%m-%d") if next_event_date else None,
        }

        return pd.DataFrame([row])

    def get_context_range(
        self,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Get events context for a date range."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        rows = []
        current = start
        while current <= end:
            ctx = self.get_context(current.strftime("%Y-%m-%d"))
            rows.append(ctx.iloc[0].to_dict())
            current += timedelta(days=1)

        return pd.DataFrame(rows)
