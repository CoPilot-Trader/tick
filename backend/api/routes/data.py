"""
Data Agent API Routes.

Provides REST endpoints for:
- Historical data backfill
- Real-time data fetching
- Data quality validation
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import data agent
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.data_agent.agent import DataAgent

router = APIRouter(prefix="/data", tags=["Data Agent"])

# Global agent instance
_data_agent: Optional[DataAgent] = None


def get_data_agent() -> DataAgent:
    """Get or create the Data Agent instance."""
    global _data_agent
    if _data_agent is None:
        _data_agent = DataAgent({
            "tickers": ["AAPL", "TSLA", "MSFT", "GOOGL", "SPY"],
            "timeframes": ["1d", "1h", "5m"],
            "storage_path": "storage/historical"
        })
        _data_agent.initialize()
    return _data_agent


# ============================================================================
# Request/Response Models
# ============================================================================

class HistoricalRequest(BaseModel):
    """Request model for historical data."""
    ticker: str = Field(..., description="Stock symbol (e.g., AAPL)")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    timeframe: str = Field("1d", description="Data interval (5m, 1h, 1d)")


class BackfillRequest(BaseModel):
    """Request model for backfill operation."""
    tickers: List[str] = Field(default=["AAPL", "TSLA", "MSFT", "GOOGL", "SPY"])
    years: int = Field(2, ge=1, le=10)
    timeframes: List[str] = Field(default=["1d"])


class DataResponse(BaseModel):
    """Response model for data operations."""
    success: bool
    symbol: str
    timeframe: str
    rows: int = 0
    pipeline: str = ""
    source: Optional[str] = None
    storage_path: Optional[str] = None
    error: Optional[str] = None


class LatestDataResponse(BaseModel):
    """Response model for latest data."""
    success: bool
    symbol: str
    timeframe: str
    bars: int = 0
    data: Optional[List[dict]] = None
    source: Optional[str] = None
    pipeline: str = ""
    error: Optional[str] = None


class QualityResponse(BaseModel):
    """Response model for data quality check."""
    symbol: str
    timeframe: str
    status: str
    quality_score: float
    total_bars: int = 0
    date_range: Optional[dict] = None
    issues: Optional[List[str]] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Data Agent health."""
    agent = get_data_agent()
    return agent.health_check()


@router.post("/historical", response_model=DataResponse)
async def fetch_historical(request: HistoricalRequest):
    """
    Fetch historical OHLCV data and store in Parquet.
    
    This is for the HISTORICAL PIPELINE (training/backtesting).
    """
    agent = get_data_agent()
    
    # Parse dates
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    
    if request.start_date:
        try:
            start_date = datetime.fromisoformat(request.start_date)
        except ValueError:
            raise HTTPException(400, f"Invalid start_date format: {request.start_date}")
    
    if request.end_date:
        try:
            end_date = datetime.fromisoformat(request.end_date)
        except ValueError:
            raise HTTPException(400, f"Invalid end_date format: {request.end_date}")
    
    result = agent.fetch_historical(
        request.ticker,
        start_date,
        end_date,
        request.timeframe
    )
    
    return DataResponse(**result)


@router.post("/backfill")
async def backfill_all(request: BackfillRequest):
    """
    Backfill historical data for multiple tickers.
    
    This is for initializing the HISTORICAL PIPELINE.
    """
    agent = get_data_agent()
    
    # Override agent tickers temporarily
    original_tickers = agent.tickers
    original_timeframes = agent.timeframes
    
    agent.tickers = request.tickers
    agent.timeframes = request.timeframes
    
    result = agent.backfill_all(request.years, request.timeframes)
    
    # Restore
    agent.tickers = original_tickers
    agent.timeframes = original_timeframes
    
    return result


@router.get("/latest/{ticker}", response_model=LatestDataResponse)
async def fetch_latest(
    ticker: str,
    timeframe: str = Query("5m", description="Data timeframe"),
    bars: int = Query(1, ge=1, le=100, description="Number of bars")
):
    """
    Fetch the most recent bars for a ticker.
    
    This is for the INFERENCE PIPELINE (live predictions).
    """
    agent = get_data_agent()
    result = agent.fetch_latest(ticker, timeframe, bars)
    return LatestDataResponse(**result)


@router.get("/quality/{ticker}", response_model=QualityResponse)
async def validate_quality(
    ticker: str,
    timeframe: str = Query("1d", description="Data timeframe")
):
    """
    Validate data quality for a ticker.
    """
    agent = get_data_agent()
    result = agent.validate_data_quality(ticker, timeframe)
    return QualityResponse(**result)


@router.get("/stored")
async def list_stored_data():
    """
    List all stored historical data.
    """
    agent = get_data_agent()
    storage = agent._storage
    
    tickers = storage.list_tickers()
    data = {}
    
    for ticker in tickers:
        timeframes = storage.list_timeframes(ticker)
        data[ticker] = {}
        for tf in timeframes:
            range_info = storage.get_data_range(ticker, tf)
            if range_info:
                data[ticker][tf] = {
                    "rows": range_info["rows"],
                    "start": range_info["start"].isoformat(),
                    "end": range_info["end"].isoformat()
                }
    
    return {
        "tickers": len(tickers),
        "data": data
    }


@router.delete("/stored/{ticker}")
async def delete_stored_data(
    ticker: str,
    timeframe: Optional[str] = Query(None, description="Specific timeframe to delete")
):
    """
    Delete stored historical data.
    """
    agent = get_data_agent()
    storage = agent._storage
    
    deleted = storage.delete_data(ticker, timeframe)
    
    return {
        "success": True,
        "ticker": ticker,
        "timeframe": timeframe or "all",
        "files_deleted": deleted
    }




