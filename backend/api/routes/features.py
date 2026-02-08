"""
Feature Agent API Routes.

Provides REST endpoints for:
- Feature calculation
- Indicator computation
- Feature caching
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.feature_agent.agent import FeatureAgent
from agents.data_agent.agent import DataAgent

router = APIRouter(prefix="/features", tags=["Feature Agent"])

# Global agent instances
_feature_agent: Optional[FeatureAgent] = None
_data_agent: Optional[DataAgent] = None


def get_feature_agent() -> FeatureAgent:
    """Get or create the Feature Agent instance."""
    global _feature_agent
    if _feature_agent is None:
        _feature_agent = FeatureAgent()
        _feature_agent.initialize()
    return _feature_agent


def get_data_agent() -> DataAgent:
    """Get or create the Data Agent instance."""
    global _data_agent
    if _data_agent is None:
        _data_agent = DataAgent({
            "storage_path": "storage/historical"
        })
        _data_agent.initialize()
    return _data_agent


# ============================================================================
# Request/Response Models
# ============================================================================

class FeatureRequest(BaseModel):
    """Request model for feature calculation."""
    ticker: str = Field(..., description="Stock symbol")
    timeframe: str = Field("1d", description="Data timeframe")
    indicators: Optional[List[str]] = Field(None, description="Specific indicators to calculate")
    include_all: bool = Field(False, description="Include all historical features in response")


class FeatureResponse(BaseModel):
    """Response model for features."""
    success: bool
    symbol: str
    timeframe: str
    feature_count: int = 0
    features: Dict[str, Any] = {}
    error: Optional[str] = None


class IndicatorListResponse(BaseModel):
    """Response model for available indicators."""
    count: int
    indicators: List[str]
    categories: Dict[str, List[str]]


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Feature Agent health."""
    agent = get_feature_agent()
    return agent.health_check()


@router.get("/indicators")
async def list_indicators():
    """
    List all available indicators.
    """
    agent = get_feature_agent()
    
    # Categorize indicators
    categories = {
        "trend": ["sma_20", "sma_50", "sma_200", "ema_9", "ema_20", "ema_50", "adx", "plus_di", "minus_di"],
        "momentum": ["rsi_14", "macd", "macd_signal", "macd_histogram", "stoch_k", "stoch_d", "cci_20", "williams_r"],
        "volatility": ["atr_14", "bb_middle", "bb_upper", "bb_lower", "hist_volatility"],
        "volume": ["obv", "vwap", "volume_ratio", "relative_volume"],
    }
    
    return IndicatorListResponse(
        count=len(agent.indicators),
        indicators=agent.indicators,
        categories=categories
    )


@router.post("/calculate", response_model=FeatureResponse)
async def calculate_features(request: FeatureRequest):
    """
    Calculate features for a ticker.
    
    Loads historical data from storage and computes all indicators.
    """
    feature_agent = get_feature_agent()
    data_agent = get_data_agent()
    
    # Load historical data
    ohlcv_df = data_agent.load_historical(request.ticker, request.timeframe)
    
    if ohlcv_df is None or ohlcv_df.empty:
        return FeatureResponse(
            success=False,
            symbol=request.ticker,
            timeframe=request.timeframe,
            error="No historical data found. Run backfill first."
        )
    
    # Calculate features
    result = feature_agent.process(request.ticker, {
        "ohlcv_data": ohlcv_df,
        "timeframe": request.timeframe,
        "indicators": request.indicators,
        "include_all": request.include_all
    })
    
    # Convert numpy types for JSON serialization
    if result.get("features"):
        features = {}
        for k, v in result["features"].items():
            try:
                if hasattr(v, "item"):  # numpy type
                    features[k] = v.item()
                elif v != v:  # NaN check
                    features[k] = None
                else:
                    features[k] = v
            except:
                features[k] = str(v)
        result["features"] = features
    
    return FeatureResponse(**result)


@router.get("/latest/{ticker}", response_model=FeatureResponse)
async def get_latest_features(
    ticker: str,
    timeframe: str = Query("5m", description="Data timeframe"),
    bars: int = Query(100, ge=10, le=500, description="Historical bars for calculation")
):
    """
    Get features for the latest data.
    
    This is for the INFERENCE PIPELINE - fetches recent data
    and calculates features for live predictions.
    """
    feature_agent = get_feature_agent()
    data_agent = get_data_agent()
    
    # Fetch latest data
    result = data_agent.fetch_latest(ticker, timeframe, bars)
    
    if not result.get("success"):
        return FeatureResponse(
            success=False,
            symbol=ticker,
            timeframe=timeframe,
            error=result.get("error", "Failed to fetch data")
        )
    
    import pandas as pd
    ohlcv_df = pd.DataFrame(result["data"])
    
    # Calculate features
    feature_result = feature_agent.process(ticker, {
        "ohlcv_data": ohlcv_df,
        "timeframe": timeframe
    })
    
    # Clean features for JSON
    if feature_result.get("features"):
        features = {}
        for k, v in feature_result["features"].items():
            try:
                if hasattr(v, "item"):
                    features[k] = v.item()
                elif v != v:
                    features[k] = None
                else:
                    features[k] = v
            except:
                features[k] = str(v)
        feature_result["features"] = features
    
    return FeatureResponse(**feature_result)


@router.get("/cached/{ticker}")
async def get_cached_features(
    ticker: str,
    timeframe: str = Query("5m", description="Data timeframe")
):
    """
    Get cached features (if available).
    
    Returns features from Redis cache without recalculation.
    """
    agent = get_feature_agent()
    cached = agent.get_cached_features(ticker, timeframe)
    
    if cached:
        return {
            "success": True,
            "symbol": ticker,
            "timeframe": timeframe,
            "source": "cache",
            "features": cached
        }
    
    return {
        "success": False,
        "symbol": ticker,
        "timeframe": timeframe,
        "error": "No cached features found"
    }




