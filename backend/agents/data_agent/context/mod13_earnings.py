"""
MOD13: Earnings Context Module

Provides ticker-level earnings calendar and surprise data.
Critical for avoiding trades around earnings volatility or capitalizing on it.

Output columns (prefix: earn_):
- days_to_earnings: Days until next earnings report
- earnings_date: Next earnings date
- earnings_time: BMO (before market open) or AMC (after market close)
- last_surprise_pct: Last quarter's earnings surprise percentage
- surprise_history_avg: Average surprise over last 4 quarters
- beat_rate_4q: Beat rate over last 4 quarters (0-1)
- is_earnings_week: Boolean flag for earnings week
- implied_move: Expected move from options (if available)
- historical_earnings_vol: Historical volatility around earnings
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class EarningsContext:
    """
    Ticker-level earnings context module.

    Uses FMP API for earnings calendar and surprise data.
    """

    def __init__(self):
        self._fmp_collector = None
        self._earnings_cache: Dict[str, pd.DataFrame] = {}
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

    def _calculate_beat_rate(self, surprises: pd.DataFrame, n_quarters: int = 4) -> float:
        """Calculate earnings beat rate over N quarters."""
        if surprises is None or surprises.empty:
            return 0.5  # Default to 50% if no data

        recent = surprises.head(n_quarters)
        if "actualEarningResult" in recent.columns and "estimatedEarning" in recent.columns:
            beats = (recent["actualEarningResult"] > recent["estimatedEarning"]).sum()
            return beats / len(recent)

        return 0.5

    def _calculate_avg_surprise(self, surprises: pd.DataFrame, n_quarters: int = 4) -> float:
        """Calculate average surprise percentage over N quarters."""
        if surprises is None or surprises.empty:
            return 0.0

        if "surprisePercentage" in surprises.columns:
            recent = surprises.head(n_quarters)
            return recent["surprisePercentage"].mean()

        return 0.0

    def get_context(
        self,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Get earnings context for tickers.

        Args:
            date: Date for context (defaults to today)
            tickers: List of tickers to get earnings for

        Returns:
            DataFrame with columns:
            - ticker, timestamp, days_to_earnings, earnings_date, earnings_time,
              last_surprise_pct, surprise_history_avg, beat_rate_4q,
              is_earnings_week, implied_move, historical_earnings_vol
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if tickers is None or len(tickers) == 0:
            logger.warning("No tickers provided for earnings context")
            return pd.DataFrame()

        current_date = datetime.strptime(date, "%Y-%m-%d")
        rows = []

        fmp = self._get_fmp_collector()

        # Fetch earnings calendar for next 30 days
        earnings_calendar = None
        if fmp:
            try:
                earnings_calendar = fmp.fetch_earnings_calendar(
                    current_date,
                    current_date + timedelta(days=30)
                )
            except Exception as e:
                logger.warning(f"Could not fetch earnings calendar: {e}")

        for ticker in tickers:
            row = {
                "ticker": ticker.upper(),
                "timestamp": current_date,
                "days_to_earnings": 999,  # Default: no upcoming earnings
                "earnings_date": None,
                "earnings_time": None,
                "last_surprise_pct": 0.0,
                "surprise_history_avg": 0.0,
                "beat_rate_4q": 0.5,
                "is_earnings_week": False,
                "implied_move": None,
                "historical_earnings_vol": None,
            }

            # Find upcoming earnings from calendar
            if earnings_calendar is not None and not earnings_calendar.empty:
                ticker_earnings = earnings_calendar[
                    earnings_calendar["symbol"] == ticker.upper()
                ]
                if not ticker_earnings.empty:
                    next_earnings = ticker_earnings.iloc[0]
                    earnings_date = pd.to_datetime(next_earnings["date"])
                    days_to_earnings = (earnings_date - current_date).days

                    row["days_to_earnings"] = max(0, days_to_earnings)
                    row["earnings_date"] = earnings_date.strftime("%Y-%m-%d")
                    row["earnings_time"] = next_earnings.get("time", "unknown")
                    row["is_earnings_week"] = days_to_earnings <= 7

            # Fetch earnings surprises for historical data
            if fmp:
                try:
                    surprises = fmp.fetch_earnings_surprises(ticker.upper(), limit=8)
                    if surprises is not None and not surprises.empty:
                        # Get last surprise
                        if "surprisePercentage" in surprises.columns:
                            row["last_surprise_pct"] = float(
                                surprises.iloc[0]["surprisePercentage"]
                            ) if not pd.isna(surprises.iloc[0]["surprisePercentage"]) else 0.0

                        # Calculate historical stats
                        row["surprise_history_avg"] = self._calculate_avg_surprise(surprises)
                        row["beat_rate_4q"] = self._calculate_beat_rate(surprises)
                except Exception as e:
                    logger.debug(f"Could not fetch surprises for {ticker}: {e}")

            rows.append(row)

        return pd.DataFrame(rows)

    def get_earnings_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """Get full earnings calendar for date range."""
        fmp = self._get_fmp_collector()
        if not fmp:
            return None

        if start_date is None:
            start_date = datetime.now()
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date is None:
            end_date = start_date + timedelta(days=14)
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        return fmp.fetch_earnings_calendar(start_date, end_date)

    def is_earnings_week(self, ticker: str, date: Optional[str] = None) -> bool:
        """Check if ticker has earnings within a week."""
        ctx = self.get_context(date=date, tickers=[ticker])
        if ctx is not None and not ctx.empty:
            return bool(ctx.iloc[0]["is_earnings_week"])
        return False
