"""
Trend Classification Agent API Router.

Provides REST endpoints for:
- BUY/SELL/HOLD classification
- Model training
- Cross-validation
- Feature importance
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import pandas as pd

# Import agents
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.trend_classification_agent.agent import TrendClassificationAgent
from agents.data_agent.agent import DataAgent
from agents.feature_agent.agent import FeatureAgent

router = APIRouter(prefix="/api/v1/trend", tags=["Trend Classification"])

# Global agent instances
_trend_agent: Optional[TrendClassificationAgent] = None
_data_agent: Optional[DataAgent] = None
_feature_agent: Optional[FeatureAgent] = None


def get_trend_agent() -> TrendClassificationAgent:
    """Get or create Trend Classification Agent instance."""
    global _trend_agent
    if _trend_agent is None:
        _trend_agent = TrendClassificationAgent()
        _trend_agent.initialize()
    return _trend_agent


def get_data_agent() -> DataAgent:
    """Get or create Data Agent instance."""
    global _data_agent
    if _data_agent is None:
        _data_agent = DataAgent()
        _data_agent.initialize()
    return _data_agent


def get_feature_agent() -> FeatureAgent:
    """Get or create Feature Agent instance."""
    global _feature_agent
    if _feature_agent is None:
        _feature_agent = FeatureAgent()
        _feature_agent.initialize()
    return _feature_agent


# ============================================================================
# Request/Response Models
# ============================================================================

class ClassifyRequest(BaseModel):
    """Request model for classification."""
    ticker: str = Field(..., description="Stock symbol (e.g., AAPL)")
    timeframe: str = Field(
        default="1d",
        description="Timeframe (1h or 1d)"
    )
    model_type: Optional[str] = Field(
        default=None,
        description="Model type (lightgbm or xgboost)"
    )


class TrainRequest(BaseModel):
    """Request model for training."""
    ticker: str = Field(..., description="Stock symbol")
    timeframe: str = Field(default="1d")
    model_types: Optional[List[str]] = Field(
        default=["lightgbm", "xgboost"],
        description="Model types to train"
    )
    days: int = Field(
        default=365,
        ge=100,
        le=1825,
        description="Days of historical data"
    )


class ClassifyResponse(BaseModel):
    """Response model for classification."""
    success: bool
    ticker: str
    timeframe: str
    signal: Optional[str] = None  # BUY, SELL, HOLD
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    model_type: Optional[str] = None
    generated_at: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Trend Classification Agent health."""
    agent = get_trend_agent()
    return agent.health_check()


@router.get("/{ticker}")
async def get_classification(
    ticker: str,
    timeframe: str = Query("1d", regex="^(1h|1d)$"),
    model_type: Optional[str] = Query(
        None,
        description="Model type (lightgbm or xgboost)"
    ),
    days: int = Query(365, ge=100, le=1825)
) -> Dict[str, Any]:
    """
    Get trend classification for a ticker.

    Returns BUY/SELL/HOLD signal with confidence and probabilities.
    """
    try:
        # Get data
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )

        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}. Need at least 100 data points."
            )

        # Calculate features
        df_with_features = feature_agent.calculate_all(df)

        # Get classification
        trend_agent = get_trend_agent()
        result = trend_agent.classify(
            symbol=ticker,
            df=df_with_features,
            timeframe=timeframe,
            model_type=model_type
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Classification failed")
            )

        return {
            "success": True,
            "ticker": ticker,
            "timeframe": timeframe,
            "signal": result.get("signal"),
            "confidence": result.get("confidence"),
            "probabilities": result.get("probabilities"),
            "model_type": result.get("model_type"),
            "generated_at": result.get("generated_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticker}/train")
async def train_classifiers(
    ticker: str,
    request: TrainRequest
) -> Dict[str, Any]:
    """
    Train classification models for a ticker.

    Trains LightGBM and/or XGBoost classifiers.
    """
    try:
        # Get data
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe=request.timeframe
        )

        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}"
            )

        # Calculate features
        df_with_features = feature_agent.calculate_all(df)

        # Train models
        trend_agent = get_trend_agent()
        result = trend_agent.train(
            symbol=ticker,
            df=df_with_features,
            timeframe=request.timeframe,
            model_types=request.model_types
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/cross-validate")
async def cross_validate(
    ticker: str,
    timeframe: str = Query("1d", regex="^(1h|1d)$"),
    n_splits: int = Query(5, ge=3, le=10),
    days: int = Query(365, ge=100, le=1825)
) -> Dict[str, Any]:
    """
    Perform cross-validation for a ticker.

    Returns fold-by-fold accuracy metrics.
    """
    try:
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )

        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}"
            )

        df_with_features = feature_agent.calculate_all(df)

        trend_agent = get_trend_agent()
        result = trend_agent.cross_validate(
            symbol=ticker,
            df=df_with_features,
            timeframe=timeframe,
            n_splits=n_splits
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/compare")
async def compare_models(
    ticker: str,
    timeframe: str = Query("1d", regex="^(1h|1d)$"),
    validation_days: int = Query(30, ge=7, le=90),
    days: int = Query(365, ge=100, le=1825)
) -> Dict[str, Any]:
    """
    Compare LightGBM vs XGBoost for a ticker.

    Returns comparison metrics and recommendation.
    """
    try:
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )

        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}"
            )

        df_with_features = feature_agent.calculate_all(df)

        trend_agent = get_trend_agent()
        result = trend_agent.compare_models(
            symbol=ticker,
            df=df_with_features,
            timeframe=timeframe,
            validation_days=validation_days
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/features")
async def get_feature_importance(
    ticker: str,
    timeframe: str = Query("1d", regex="^(1h|1d)$"),
    top_n: int = Query(10, ge=5, le=30)
) -> Dict[str, Any]:
    """Get feature importance from trained classifier."""
    trend_agent = get_trend_agent()
    return trend_agent.get_feature_importance(
        symbol=ticker,
        timeframe=timeframe,
        top_n=top_n
    )


@router.get("/{ticker}/info")
async def get_model_info(
    ticker: str,
    timeframe: str = Query("1d", regex="^(1h|1d)$")
) -> Dict[str, Any]:
    """Get information about trained classifiers for a ticker."""
    trend_agent = get_trend_agent()
    return trend_agent.get_model_info(ticker, timeframe)


@router.post("/clear-cache")
async def clear_cache(ticker: Optional[str] = None) -> Dict[str, str]:
    """Clear cached classifiers."""
    trend_agent = get_trend_agent()
    trend_agent.clear_cache(ticker)
    return {
        "status": "success",
        "message": f"Cache cleared for {ticker if ticker else 'all tickers'}"
    }
