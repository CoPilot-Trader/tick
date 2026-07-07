"""
Data Agent API Router.

Provides REST endpoint for fetching OHLCV data.
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.data_agent.agent import DataAgent
from api.middleware.response_cache import cache_key, cache_get, cache_set

router = APIRouter(prefix="/api/v1/data", tags=["Data"])

_data_agent: Optional[DataAgent] = None


def get_data_agent() -> DataAgent:
    global _data_agent
    if _data_agent is None:
        _data_agent = DataAgent()
        _data_agent.initialize()
    return _data_agent


@router.get("/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query("5m", description="Candle timeframe: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mo"),
    days: int = Query(1, ge=1, le=3650, description="Number of days of data (capped per timeframe)"),
):
    """
    Get OHLCV data for a symbol.

    Returns array of {timestamp, open, high, low, close, volume}.
    """
    try:
        # Per-timeframe day clamps. yfinance's documented hard limits for
        # intraday are 7d (1m), 59d (5m/15m/30m). Going over silently returns
        # empty, which trips our mock-data fallback and serves stale 2023
        # prices as if they were current. Clamp inside the real window with
        # safety buffer so we never trip that path on a borderline request.
        TF_MAX_DAYS = {
            "1m": 5,
            "5m": 50, "15m": 50, "30m": 50,
            "1h": 700, "60m": 700, "4h": 700,
            "1d": 3650, "daily": 3650,
            "1wk": 3650, "1mo": 3650,
        }
        max_days = TF_MAX_DAYS.get(timeframe, 50)
        days = min(days, max_days)

        # Check cache first (60s TTL for intraday, 300s for daily)
        ck = cache_key("ohlcv", symbol=symbol, timeframe=timeframe, days=days)
        cached = cache_get(ck)
        if cached:
            return cached

        data_agent = get_data_agent()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
        )

        if df is None or len(df) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {symbol}",
            )

        # Convert DataFrame to list of dicts
        # Timestamp may be in 'bar_ts' column, 'timestamp' column, or the index
        records = []
        has_bar_ts = "bar_ts" in df.columns
        has_timestamp_col = "timestamp" in df.columns
        for idx, row in df.iterrows():
            if has_bar_ts:
                ts = row["bar_ts"]
            elif has_timestamp_col:
                ts = row["timestamp"]
            else:
                ts = idx  # timestamp is the index
            if hasattr(ts, "isoformat"):
                ts = ts.isoformat()
            else:
                ts = str(ts)
            records.append({
                "timestamp": ts,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("volume", 0)),
            })

        # If mock data returned more records than expected for the timeframe,
        # trim to the most recent ones appropriate for the request.
        # Bars-per-trading-day reference (RTH only):
        #   1m=390, 5m=78, 15m=26, 30m=13, 1h=7, 4h=2, 1d=1
        # Weekly/monthly are <1/day. A 1.5x buffer keeps any extended-hours bars.
        bars_per_day = {
            "1m": 390,
            "5m": 78,
            "15m": 26,
            "30m": 13,
            "1h": 7, "60m": 7,
            "4h": 2,
            "1d": 1, "daily": 1,
            "1wk": 1 / 5,
            "1mo": 1 / 22,
        }.get(timeframe, 1)
        max_bars = max(int(days * bars_per_day * 1.5), 100)
        if len(records) > max_bars:
            records = records[-max_bars:]

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(records),
            "data": records,
        }
        # Cache TTL — intraday bars move minute-to-minute during market
        # hours, so a 5-minute cache made the chart look 5 minutes stale
        # right after a bar closed (Tory saw last bar Jul 2 when new bar
        # was already live). Daily+ bars don't need to refresh that fast.
        intraday = timeframe in {"1m", "5m", "15m", "30m", "1h", "60m", "4h"}
        ttl = 60 if intraday else 300
        cache_set(ck, result, ttl)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
