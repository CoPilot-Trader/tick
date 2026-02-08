"""
FRED (Federal Reserve Economic Data) Collector for TICK Data Agent.

Primary source for economic indicators used in MOD09 (Macro) and MOD14 (Economic).

API Documentation: https://fred.stlouisfed.org/docs/api/fred/
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)

# Try to import pandas_datareader for FRED access
try:
    import pandas_datareader.data as web
    PANDAS_DATAREADER_AVAILABLE = True
except ImportError:
    PANDAS_DATAREADER_AVAILABLE = False
    logger.warning("pandas_datareader not installed. FRED collector will use requests fallback.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class FREDCollector:
    """
    Data collector for Federal Reserve Economic Data (FRED).

    Supports:
    - VIX (via ^VIX on yfinance, or VIXCLS on FRED)
    - Treasury yields (DGS2, DGS10, DGS30)
    - Federal funds rate (FEDFUNDS)
    - Unemployment rate (UNRATE)
    - CPI (CPIAUCSL)
    - Consumer sentiment (UMCSENT)
    - GDP (GDP, GDPC1)

    No rate limits for public FRED API.
    """

    BASE_URL = "https://api.stlouisfed.org/fred"

    # Common FRED series IDs
    SERIES_MAP = {
        # Yields and rates
        "vix": "VIXCLS",
        "fed_funds": "FEDFUNDS",
        "treasury_2y": "DGS2",
        "treasury_10y": "DGS10",
        "treasury_30y": "DGS30",

        # Employment
        "unemployment": "UNRATE",
        "initial_claims": "ICSA",
        "nonfarm_payrolls": "PAYEMS",

        # Inflation
        "cpi": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "pce": "PCEPI",

        # Consumer
        "consumer_sentiment": "UMCSENT",
        "retail_sales": "RSXFS",

        # GDP
        "gdp": "GDP",
        "real_gdp": "GDPC1",

        # Other
        "industrial_production": "INDPRO",
        "housing_starts": "HOUST",
        "dollar_index": "DTWEXBGS",
    }

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.name = "fred"
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        self.config = config or {}
        self._initialized = False
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_ttl = timedelta(hours=24)  # Economic data doesn't change often
        self._cache_timestamps: Dict[str, datetime] = {}

    def initialize(self) -> bool:
        """Initialize the FRED collector."""
        # FRED works without API key for basic access via pandas_datareader
        if not PANDAS_DATAREADER_AVAILABLE and not REQUESTS_AVAILABLE:
            logger.error("Neither pandas_datareader nor requests available for FRED")
            self._initialized = False
            return False

        self._initialized = True
        logger.info("FREDCollector initialized")
        return True

    def _get_from_cache(self, series_id: str) -> Optional[pd.DataFrame]:
        """Get data from cache if still valid."""
        if series_id in self._cache:
            cached_at = self._cache_timestamps.get(series_id)
            if cached_at and (datetime.now() - cached_at) < self._cache_ttl:
                return self._cache[series_id].copy()
        return None

    def _put_in_cache(self, series_id: str, df: pd.DataFrame) -> None:
        """Store data in cache."""
        self._cache[series_id] = df.copy()
        self._cache_timestamps[series_id] = datetime.now()

    def fetch_series(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch a FRED data series.

        Args:
            series_id: FRED series ID (e.g., "DGS10" for 10-year treasury)
            start_date: Start date (defaults to 1 year ago)
            end_date: End date (defaults to today)

        Returns:
            DataFrame with columns [date, value]
        """
        if not self._initialized:
            logger.error("FRED collector not initialized")
            return None

        # Check cache
        cached = self._get_from_cache(series_id)
        if cached is not None:
            # Filter cached data by date range
            if start_date:
                cached = cached[cached["date"] >= start_date]
            if end_date:
                cached = cached[cached["date"] <= end_date]
            return cached

        # Set defaults
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        try:
            if PANDAS_DATAREADER_AVAILABLE:
                # Use pandas_datareader
                df = web.DataReader(series_id, "fred", start_date, end_date)
                df = df.reset_index()
                df.columns = ["date", "value"]
                df["series_id"] = series_id
            elif self.api_key and REQUESTS_AVAILABLE:
                # Fallback to direct API call
                df = self._fetch_via_api(series_id, start_date, end_date)
            else:
                logger.error("No method available to fetch FRED data")
                return None

            if df is not None and not df.empty:
                self._put_in_cache(series_id, df)

            return df

        except Exception as e:
            logger.error(f"FRED fetch error for {series_id}: {e}")
            return None

    def _fetch_via_api(
        self,
        series_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Fetch data directly from FRED API."""
        if not self.api_key:
            logger.error("FRED API key required for direct API access")
            return None

        url = f"{self.BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date.strftime("%Y-%m-%d"),
            "observation_end": end_date.strftime("%Y-%m-%d"),
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])
            if not observations:
                return None

            df = pd.DataFrame(observations)
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["series_id"] = series_id
            df = df[["date", "value", "series_id"]]

            return df

        except Exception as e:
            logger.error(f"FRED API error: {e}")
            return None

    # =========================================================================
    # CONVENIENCE METHODS FOR COMMON SERIES
    # =========================================================================

    def fetch_vix(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """Fetch VIX data (VIXCLS series)."""
        return self.fetch_series("VIXCLS", start_date, end_date)

    def fetch_treasury_yields(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch treasury yield data (2Y, 10Y, 30Y).

        Returns DataFrame with columns: date, yield_2y, yield_10y, yield_30y
        """
        dfs = []
        for name, series_id in [
            ("yield_2y", "DGS2"),
            ("yield_10y", "DGS10"),
            ("yield_30y", "DGS30"),
        ]:
            df = self.fetch_series(series_id, start_date, end_date)
            if df is not None:
                df = df.rename(columns={"value": name})
                df = df[["date", name]]
                dfs.append(df)

        if not dfs:
            return None

        # Merge all yield series
        result = dfs[0]
        for df in dfs[1:]:
            result = result.merge(df, on="date", how="outer")

        result = result.sort_values("date")

        # Calculate yield curve spread (10Y - 2Y)
        if "yield_10y" in result.columns and "yield_2y" in result.columns:
            result["yield_spread_2s10s"] = result["yield_10y"] - result["yield_2y"]
            result["yield_curve_inverted"] = result["yield_spread_2s10s"] < 0

        return result

    def fetch_fed_funds_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """Fetch Federal Funds Rate."""
        df = self.fetch_series("FEDFUNDS", start_date, end_date)
        if df is not None:
            df = df.rename(columns={"value": "fed_funds_rate"})
        return df

    def fetch_unemployment(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """Fetch unemployment rate."""
        df = self.fetch_series("UNRATE", start_date, end_date)
        if df is not None:
            df = df.rename(columns={"value": "unemployment_rate"})
        return df

    def fetch_cpi(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch CPI data and calculate YoY change.
        """
        df = self.fetch_series("CPIAUCSL", start_date, end_date)
        if df is None:
            return None

        df = df.rename(columns={"value": "cpi"})

        # Calculate YoY change (need 12 months of history)
        df = df.sort_values("date")
        df["cpi_yoy"] = df["cpi"].pct_change(periods=12) * 100
        df["cpi_mom"] = df["cpi"].pct_change(periods=1) * 100

        return df

    def fetch_consumer_sentiment(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """Fetch University of Michigan Consumer Sentiment."""
        df = self.fetch_series("UMCSENT", start_date, end_date)
        if df is not None:
            df = df.rename(columns={"value": "consumer_sentiment"})
            df["sentiment_change_mom"] = df["consumer_sentiment"].diff()
        return df

    def fetch_economic_indicators(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch all major economic indicators for MOD14.

        Returns combined DataFrame with all indicators.
        """
        indicators = {}

        # Treasury yields
        yields = self.fetch_treasury_yields(start_date, end_date)
        if yields is not None:
            indicators["yields"] = yields

        # Fed funds
        fed = self.fetch_fed_funds_rate(start_date, end_date)
        if fed is not None:
            indicators["fed"] = fed[["date", "fed_funds_rate"]]

        # Unemployment
        unemp = self.fetch_unemployment(start_date, end_date)
        if unemp is not None:
            indicators["unemp"] = unemp[["date", "unemployment_rate"]]

        # CPI
        cpi = self.fetch_cpi(start_date, end_date)
        if cpi is not None:
            indicators["cpi"] = cpi[["date", "cpi_yoy", "cpi_mom"]]

        # Consumer sentiment
        sentiment = self.fetch_consumer_sentiment(start_date, end_date)
        if sentiment is not None:
            indicators["sentiment"] = sentiment[["date", "consumer_sentiment"]]

        if not indicators:
            return None

        # Merge all indicators on date
        result = None
        for name, df in indicators.items():
            if result is None:
                result = df
            else:
                result = result.merge(df, on="date", how="outer")

        if result is not None:
            result = result.sort_values("date")
            # Forward fill economic data (published monthly/quarterly)
            result = result.ffill()

        return result

    def health_check(self) -> Dict[str, Any]:
        """Check if FRED is operational."""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "collector": self.name
            }

        try:
            # Test with a simple fetch
            df = self.fetch_series("DGS10", datetime.now() - timedelta(days=7), datetime.now())

            if df is not None and not df.empty:
                return {
                    "status": "healthy",
                    "collector": self.name,
                    "test_series": "DGS10",
                    "latest_value": float(df["value"].iloc[-1]) if not df.empty else None
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
