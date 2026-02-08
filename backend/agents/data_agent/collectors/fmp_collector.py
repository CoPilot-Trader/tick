"""
FMP (Financial Modeling Prep) Collector for TICK Data Agent.

Primary source for earnings data, company profiles, and fundamentals.
Used for MOD06 (Events) and MOD13 (Earnings) context modules.

API Documentation: https://financialmodelingprep.com/developer/docs/
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import requests

from .base import BaseCollector, CollectorResult

logger = logging.getLogger(__name__)


class FMPCollector(BaseCollector):
    """
    Data collector using Financial Modeling Prep API.

    Supports:
    - Historical price data
    - Earnings calendar and surprises
    - Company profiles
    - Sector performance
    - Economic calendar (FOMC, CPI dates)

    Rate Limits (Free Tier):
    - 250 API calls/day
    - 5 calls/second
    """

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="fmp", config=config)
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        self._session: Optional[requests.Session] = None

    def initialize(self) -> bool:
        """Initialize the FMP collector."""
        if not self.api_key:
            logger.error("FMP API key not provided")
            self._initialized = False
            return False

        self._session = requests.Session()
        self._initialized = True
        logger.info("FMPCollector initialized")
        return True

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Make authenticated request to FMP API."""
        if not self._initialized:
            return None

        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["apikey"] = self.api_key

        try:
            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"FMP request failed for {endpoint}: {e}")
            return None

    def fetch_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> CollectorResult:
        """
        Fetch historical price data from FMP.

        Note: FMP is primarily used for fundamentals, not price data.
        For price data, prefer Tiingo or yfinance.
        """
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized"
            )

        try:
            # FMP historical endpoint
            data = self._make_request(
                f"historical-price-full/{ticker}",
                params={
                    "from": start_date.strftime("%Y-%m-%d"),
                    "to": end_date.strftime("%Y-%m-%d"),
                }
            )

            if not data or "historical" not in data:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No historical data for {ticker}"
                )

            df = pd.DataFrame(data["historical"])

            # Rename columns
            df = df.rename(columns={
                "date": "bar_ts",
                "adjClose": "close",
            })

            # FMP returns data in reverse chronological order
            df = df.sort_values("bar_ts")

            normalized_df = self._normalize_dataframe(df, ticker, timeframe)

            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else start_date,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else end_date,
                source="fmp",
            )

        except Exception as e:
            logger.error(f"FMP historical error for {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )

    def fetch_latest(
        self,
        ticker: str,
        timeframe: str = "1d",
        bars: int = 1
    ) -> CollectorResult:
        """Fetch latest price data."""
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized"
            )

        try:
            data = self._make_request(f"quote/{ticker}")

            if not data or len(data) == 0:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No quote data for {ticker}"
                )

            quote = data[0]
            df = pd.DataFrame([{
                "bar_ts": datetime.now(),
                "open": quote.get("open"),
                "high": quote.get("dayHigh"),
                "low": quote.get("dayLow"),
                "close": quote.get("price"),
                "volume": quote.get("volume"),
            }])

            normalized_df = self._normalize_dataframe(df, ticker, timeframe)

            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=1,
                source="fmp",
            )

        except Exception as e:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )

    # =========================================================================
    # EARNINGS DATA (for MOD13)
    # =========================================================================

    def fetch_earnings_calendar(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch earnings calendar for date range.

        Returns DataFrame with columns:
        - symbol, date, time (bmo/amc), epsEstimated, epsActual, revenueEstimated, revenueActual
        """
        if from_date is None:
            from_date = datetime.now()
        if to_date is None:
            to_date = from_date + timedelta(days=30)

        data = self._make_request(
            "earning_calendar",
            params={
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
            }
        )

        if not data:
            return None

        df = pd.DataFrame(data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def fetch_earnings_surprises(self, ticker: str, limit: int = 10) -> Optional[pd.DataFrame]:
        """
        Fetch historical earnings surprises for a ticker.

        Returns DataFrame with:
        - date, actualEarningResult, estimatedEarning, surprisePercent
        """
        data = self._make_request(f"earnings-surprises/{ticker}")

        if not data:
            return None

        df = pd.DataFrame(data[:limit])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def fetch_earnings_confirmed(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """Fetch confirmed earnings dates."""
        if from_date is None:
            from_date = datetime.now()
        if to_date is None:
            to_date = from_date + timedelta(days=14)

        data = self._make_request(
            "earning-calendar-confirmed",
            params={
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
            }
        )

        if not data:
            return None

        return pd.DataFrame(data)

    # =========================================================================
    # ECONOMIC CALENDAR (for MOD06)
    # =========================================================================

    def fetch_economic_calendar(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch economic calendar (FOMC, CPI, Jobs, GDP events).

        Returns DataFrame with:
        - date, event, country, actual, previous, estimate, impact
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=7)
        if to_date is None:
            to_date = datetime.now() + timedelta(days=30)

        data = self._make_request(
            "economic_calendar",
            params={
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
            }
        )

        if not data:
            return None

        df = pd.DataFrame(data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            # Filter for US events only
            df = df[df["country"] == "US"]
        return df

    # =========================================================================
    # COMPANY DATA
    # =========================================================================

    def fetch_company_profile(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company profile (sector, industry, etc.).
        """
        data = self._make_request(f"profile/{ticker}")

        if not data or len(data) == 0:
            return None

        profile = data[0]
        return {
            "ticker": profile.get("symbol"),
            "name": profile.get("companyName"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "exchange": profile.get("exchangeShortName"),
            "market_cap": profile.get("mktCap"),
            "beta": profile.get("beta"),
            "description": profile.get("description"),
        }

    def fetch_sector_performance(self) -> Optional[pd.DataFrame]:
        """
        Fetch sector performance data for MOD11 (Sector Rotation).
        """
        data = self._make_request("sector-performance")

        if not data:
            return None

        df = pd.DataFrame(data)
        # Convert percentage strings to floats
        if "changesPercentage" in df.columns:
            df["changesPercentage"] = df["changesPercentage"].str.rstrip("%").astype(float)
        return df

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check if FMP API is operational."""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "collector": self.name
            }

        try:
            data = self._make_request("quote/AAPL")

            if data and len(data) > 0:
                return {
                    "status": "healthy",
                    "collector": self.name,
                    "test_ticker": "AAPL",
                    "price": data[0].get("price")
                }
            else:
                return {
                    "status": "degraded",
                    "collector": self.name,
                    "error": "No data returned"
                }

        except Exception as e:
            return {
                "status": "error",
                "collector": self.name,
                "error": str(e)
            }
