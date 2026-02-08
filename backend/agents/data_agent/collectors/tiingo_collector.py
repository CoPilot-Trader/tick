"""
Tiingo Collector for TICK Data Agent.

Primary data source for historical and real-time OHLCV data.
Tiingo provides high-quality EOD and IEX intraday data.

API Documentation: https://api.tiingo.com/documentation/general/overview
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import requests

from .base import BaseCollector, CollectorResult

logger = logging.getLogger(__name__)


class TiingoCollector(BaseCollector):
    """
    Data collector using Tiingo API.

    Supports:
    - EOD (End of Day) historical data - unlimited history
    - IEX intraday data - supports 1min, 5min, 15min, 30min, 1hour
    - Real-time quotes via IEX

    Rate Limits (Free Tier):
    - 500 requests/hour
    - 20,000 requests/month
    """

    BASE_URL = "https://api.tiingo.com"

    # Tiingo IEX resample frequencies
    IEX_RESAMPLE_MAP = {
        "1m": "1min",
        "1min": "1min",
        "5m": "5min",
        "5min": "5min",
        "15m": "15min",
        "15min": "15min",
        "30m": "30min",
        "30min": "30min",
        "1h": "1hour",
        "1hour": "1hour",
        "60m": "1hour",
    }

    # Maximum history for IEX (intraday)
    IEX_MAX_HISTORY_DAYS = 30  # Tiingo IEX historical limit

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="tiingo", config=config)
        self.api_key = api_key or os.getenv("TIINGO_API_KEY")
        self._session: Optional[requests.Session] = None

    def initialize(self) -> bool:
        """Initialize the Tiingo collector."""
        if not self.api_key:
            logger.error("Tiingo API key not provided")
            self._initialized = False
            return False

        # Create session with auth headers
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        })

        self._initialized = True
        logger.info("TiingoCollector initialized")
        return True

    def fetch_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> CollectorResult:
        """
        Fetch historical OHLCV data from Tiingo.

        For daily data, uses the EOD endpoint.
        For intraday data, uses the IEX endpoint.
        """
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized"
            )

        # Route to appropriate endpoint based on timeframe
        if timeframe in ["1d", "daily", "1wk", "1mo"]:
            return self._fetch_eod(ticker, start_date, end_date, timeframe)
        else:
            return self._fetch_iex_historical(ticker, start_date, end_date, timeframe)

    def _fetch_eod(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> CollectorResult:
        """Fetch end-of-day historical data."""
        try:
            url = f"{self.BASE_URL}/tiingo/daily/{ticker}/prices"
            params = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
            }

            response = self._session.get(url, params=params, timeout=30)

            if response.status_code == 404:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"Ticker {ticker} not found on Tiingo"
                )

            response.raise_for_status()
            data = response.json()

            if not data:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No EOD data returned for {ticker}"
                )

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Rename columns to standard format
            df = df.rename(columns={
                "date": "bar_ts",
                "adjOpen": "open",
                "adjHigh": "high",
                "adjLow": "low",
                "adjClose": "close",
                "adjVolume": "volume",
            })

            # Use adjusted prices by default
            # Fallback to unadjusted if adjusted not available
            for col in ["open", "high", "low", "close", "volume"]:
                if col not in df.columns:
                    unadj_col = col if col != "volume" else "volume"
                    if unadj_col in df.columns:
                        df[col] = df[unadj_col]

            # Normalize
            normalized_df = self._normalize_dataframe(df, ticker, timeframe)

            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else start_date,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else end_date,
                source="tiingo_eod",
                metadata={"adjusted": True}
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Tiingo EOD request failed for {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Tiingo EOD error for {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )

    def _fetch_iex_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "5min"
    ) -> CollectorResult:
        """Fetch intraday historical data via IEX."""
        try:
            # Map timeframe to Tiingo resample frequency
            resample_freq = self.IEX_RESAMPLE_MAP.get(timeframe)
            if not resample_freq:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"Unsupported intraday timeframe: {timeframe}"
                )

            # Check history limits
            max_start = datetime.now() - timedelta(days=self.IEX_MAX_HISTORY_DAYS)
            if start_date < max_start:
                logger.warning(
                    f"Adjusting start_date for {ticker} IEX: {start_date} -> {max_start}"
                )
                start_date = max_start

            url = f"{self.BASE_URL}/iex/{ticker}/prices"
            params = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "resampleFreq": resample_freq,
            }

            response = self._session.get(url, params=params, timeout=60)

            if response.status_code == 404:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"Ticker {ticker} not found on Tiingo IEX"
                )

            response.raise_for_status()
            data = response.json()

            if not data:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No IEX data returned for {ticker}"
                )

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Rename columns
            df = df.rename(columns={
                "date": "bar_ts",
            })

            # Normalize
            normalized_df = self._normalize_dataframe(df, ticker, timeframe)

            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else start_date,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else end_date,
                source="tiingo_iex",
                metadata={"resample_freq": resample_freq}
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Tiingo IEX request failed for {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Tiingo IEX error for {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )

    def fetch_latest(
        self,
        ticker: str,
        timeframe: str = "5min",
        bars: int = 1
    ) -> CollectorResult:
        """
        Fetch the most recent bars via IEX.
        """
        if not self._initialized:
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error="Collector not initialized"
            )

        try:
            # For latest data, use IEX endpoint
            url = f"{self.BASE_URL}/iex/{ticker}/prices"

            resample_freq = self.IEX_RESAMPLE_MAP.get(timeframe, "5min")

            params = {
                "resampleFreq": resample_freq,
            }

            response = self._session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not data:
                return CollectorResult(
                    success=False,
                    ticker=ticker,
                    timeframe=timeframe,
                    error=f"No latest data for {ticker}"
                )

            # Take only the requested number of bars
            df = pd.DataFrame(data[-bars:] if len(data) >= bars else data)
            df = df.rename(columns={"date": "bar_ts"})

            normalized_df = self._normalize_dataframe(df, ticker, timeframe)

            return CollectorResult(
                success=True,
                ticker=ticker,
                timeframe=timeframe,
                data=normalized_df,
                rows_fetched=len(normalized_df),
                start_date=normalized_df["bar_ts"].min() if len(normalized_df) > 0 else None,
                end_date=normalized_df["bar_ts"].max() if len(normalized_df) > 0 else None,
                source="tiingo_iex",
                metadata={"bars_requested": bars}
            )

        except Exception as e:
            logger.error(f"Tiingo fetch_latest error for {ticker}: {e}")
            return CollectorResult(
                success=False,
                ticker=ticker,
                timeframe=timeframe,
                error=str(e)
            )

    def fetch_metadata(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch ticker metadata (company info, exchange, etc.).
        """
        if not self._initialized:
            return {"error": "Collector not initialized"}

        try:
            url = f"{self.BASE_URL}/tiingo/daily/{ticker}"
            response = self._session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            return {
                "ticker": data.get("ticker"),
                "name": data.get("name"),
                "exchange": data.get("exchangeCode"),
                "description": data.get("description"),
                "start_date": data.get("startDate"),
                "end_date": data.get("endDate"),
            }

        except Exception as e:
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Check if Tiingo API is operational."""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "collector": self.name
            }

        try:
            # Test with a simple metadata request
            url = f"{self.BASE_URL}/tiingo/daily/AAPL"
            response = self._session.get(url, timeout=10)

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "collector": self.name,
                    "test_ticker": "AAPL"
                }
            elif response.status_code == 401:
                return {
                    "status": "auth_failed",
                    "collector": self.name,
                    "error": "Invalid API key"
                }
            else:
                return {
                    "status": "degraded",
                    "collector": self.name,
                    "http_status": response.status_code
                }

        except Exception as e:
            return {
                "status": "error",
                "collector": self.name,
                "error": str(e)
            }
