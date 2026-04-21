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
    timeframe: str = Query("5m", description="Candle timeframe: 5m, 1h, 1d"),
    days: int = Query(1, ge=1, le=60, description="Number of days of data"),
):
    """
    Get OHLCV data for a symbol.

    Returns array of {timestamp, open, high, low, close, volume}.
    """
    try:
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
        # trim to the most recent ones appropriate for the request
        if timeframe == "5m":
            max_bars = days * 78  # ~78 five-min bars per trading day
        elif timeframe == "1h":
            max_bars = days * 7  # ~7 hourly bars per trading day
        else:
            max_bars = days
        if len(records) > max_bars:
            records = records[-max_bars:]

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(records),
            "data": records,
        }
        ttl = 60 if timeframe == "5m" else 300
        cache_set(ck, result, ttl)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
