"""
Price Forecast Agent API Router.

Provides REST endpoints for:
- Price predictions (multi-horizon)
- Model training
- Model comparison
- Health checks
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import pandas as pd

# Import agent
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.price_forecast_agent.agent import PriceForecastAgent
from agents.data_agent.agent import DataAgent

router = APIRouter(prefix="/api/v1/forecast", tags=["Price Forecast"])

# Global agent instances
_forecast_agent: Optional[PriceForecastAgent] = None
_data_agent: Optional[DataAgent] = None


def get_forecast_agent() -> PriceForecastAgent:
    """Get or create Price Forecast Agent instance."""
    global _forecast_agent
    if _forecast_agent is None:
        _forecast_agent = PriceForecastAgent()
        _forecast_agent.initialize()
    return _forecast_agent


def get_data_agent() -> DataAgent:
    """Get or create Data Agent instance."""
    global _data_agent
    if _data_agent is None:
        _data_agent = DataAgent()
        _data_agent.initialize()
    return _data_agent


# ============================================================================
# Request/Response Models
# ============================================================================

class PredictionRequest(BaseModel):
    """Request model for predictions."""
    ticker: str = Field(..., description="Stock symbol (e.g., AAPL)")
    horizons: Optional[List[str]] = Field(
        default=["1h", "4h", "1d", "1w"],
        description="Prediction horizons"
    )
    use_baseline: bool = Field(
        default=False,
        description="Use Prophet baseline instead of LSTM"
    )
    use_ensemble: bool = Field(
        default=True,
        description="Use ensemble of Prophet + LSTM"
    )


class TrainRequest(BaseModel):
    """Request model for training."""
    ticker: str = Field(..., description="Stock symbol")
    walk_forward: bool = Field(
        default=True,
        description="Use walk-forward validation"
    )
    days: int = Field(
        default=365,
        ge=60,
        le=1825,
        description="Days of historical data for training"
    )


class PredictionResponse(BaseModel):
    """Response model for predictions."""
    success: bool
    ticker: str
    current_price: Optional[float] = None
    predictions: Optional[Dict[str, Any]] = None
    model_type: Optional[str] = None
    generated_at: Optional[str] = None
    error: Optional[str] = None


class TrainResponse(BaseModel):
    """Response model for training."""
    success: bool
    ticker: str
    models: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Price Forecast Agent health."""
    agent = get_forecast_agent()
    return agent.health_check()


@router.get("/{ticker}")
async def get_prediction(
    ticker: str,
    horizons: Optional[str] = Query(
        "1h,4h,1d,1w",
        description="Comma-separated horizons"
    ),
    use_baseline: bool = Query(False),
    use_ensemble: bool = Query(True),
    days: int = Query(365, ge=60, le=1825)
) -> Dict[str, Any]:
    """
    Get price predictions for a ticker.

    Returns predictions for specified horizons with confidence intervals.
    """
    try:
        # Parse horizons
        horizon_list = [h.strip() for h in horizons.split(",")]

        # Get data
        data_agent = get_data_agent()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d"
        )

        if df is None or len(df) < 60:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}. Need at least 60 data points."
            )

        # Get predictions
        forecast_agent = get_forecast_agent()
        result = forecast_agent.predict(
            symbol=ticker,
            df=df,
            horizons=horizon_list,
            use_baseline=use_baseline,
            use_ensemble=use_ensemble
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Prediction failed")
            )

        return {
            "success": True,
            "ticker": ticker,
            "current_price": result.get("current_price"),
            "predictions": result.get("predictions"),
            "model_type": result.get("model_type"),
            "generated_at": result.get("generated_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticker}/train")
async def train_models(
    ticker: str,
    request: TrainRequest
) -> Dict[str, Any]:
    """
    Train prediction models for a ticker.

    Trains both Prophet and LSTM models with optional walk-forward validation.
    """
    try:
        # Get data
        data_agent = get_data_agent()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d"
        )

        if df is None or len(df) < 60:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}"
            )

        # Train models
        forecast_agent = get_forecast_agent()
        result = forecast_agent.train_models(
            symbol=ticker,
            df=df,
            walk_forward=request.walk_forward
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/compare")
async def compare_models(
    ticker: str,
    validation_days: int = Query(30, ge=7, le=90),
    days: int = Query(365, ge=60, le=1825)
) -> Dict[str, Any]:
    """
    Compare Prophet vs LSTM models for a ticker.

    Returns comparison metrics and recommendation.
    """
    try:
        data_agent = get_data_agent()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d"
        )

        if df is None or len(df) < 60:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}"
            )

        forecast_agent = get_forecast_agent()
        result = forecast_agent.compare_models(
            symbol=ticker,
            df=df,
            validation_days=validation_days
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/info")
async def get_model_info(ticker: str) -> Dict[str, Any]:
    """Get information about trained models for a ticker."""
    forecast_agent = get_forecast_agent()
    return forecast_agent.get_model_info(ticker)


@router.post("/clear-cache")
async def clear_cache(ticker: Optional[str] = None) -> Dict[str, str]:
    """Clear cached models."""
    forecast_agent = get_forecast_agent()
    forecast_agent.clear_cache(ticker)
    return {
        "status": "success",
        "message": f"Cache cleared for {ticker if ticker else 'all tickers'}"
    }
