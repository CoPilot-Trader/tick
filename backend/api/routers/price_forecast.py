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
import json
import os

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

        # Log prediction for backtracking
        try:
            if result.get("predictions") and result.get("current_price"):
                _store_prediction(ticker, result["current_price"], result["predictions"])
        except Exception:
            pass  # Don't fail the request if logging fails

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


# ============================================================================
# Prediction History / Backtracking
# ============================================================================

PREDICTION_LOG_DIR = Path(__file__).parent.parent.parent / "storage" / "prediction_logs"
PREDICTION_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _log_path(ticker: str) -> Path:
    return PREDICTION_LOG_DIR / f"{ticker.upper()}_predictions.json"


def _load_log(ticker: str) -> List[Dict[str, Any]]:
    path = _log_path(ticker)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return []
    return []


def _save_log(ticker: str, entries: List[Dict[str, Any]]):
    path = _log_path(ticker)
    # Keep last 2000 entries max (~7 days of 5-min predictions)
    entries = entries[-2000:]
    path.write_text(json.dumps(entries, default=str))


def _store_prediction(ticker: str, current_price: float, predictions: Dict[str, Any]):
    """Store a prediction for later backtracking."""
    entries = _load_log(ticker)
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "current_price": current_price,
        "predictions": {},
    }
    for horizon, pred in predictions.items():
        entry["predictions"][horizon] = {
            "predicted_price": pred.get("price", pred.get("predicted_price")),
            "confidence": pred.get("confidence", 0),
            "direction": pred.get("direction", "NEUTRAL"),
            "upper": pred.get("price_upper", pred.get("upper_bound")),
            "lower": pred.get("price_lower", pred.get("lower_bound")),
        }
    entries.append(entry)
    _save_log(ticker, entries)


@router.get("/{ticker}/history")
async def get_prediction_history(
    ticker: str,
    limit: int = Query(500, ge=1, le=2000),
) -> Dict[str, Any]:
    """
    Get prediction history with actual price comparison.

    Returns past predictions alongside what the actual price turned out to be,
    so we can see the gap between predicted and actual.
    """
    try:
        entries = _load_log(ticker)
        if not entries:
            return {
                "status": "success",
                "symbol": ticker,
                "count": 0,
                "predictions": [],
                "accuracy": None,
            }

        # Get current price data for backtracking (both daily and intraday)
        data_agent = get_data_agent()
        end_date = datetime.now()

        # Daily data for 1d/1w horizon matching
        start_date_daily = end_date - timedelta(days=30)
        df_daily = data_agent.fetch_historical_sync(
            symbol=ticker, start_date=start_date_daily, end_date=end_date, timeframe="1d"
        )

        # Intraday data (5m bars, last 2 days) for 1h/4h horizon matching
        start_date_intraday = end_date - timedelta(days=2)
        df_intraday = None
        try:
            df_intraday = data_agent.fetch_historical_sync(
                symbol=ticker, start_date=start_date_intraday, end_date=end_date, timeframe="5m"
            )
        except Exception:
            pass

        # Build date->price lookup from daily data
        actual_prices: Dict[str, float] = {}
        if df_daily is not None and len(df_daily) > 0:
            for idx, row in df_daily.iterrows():
                ts = row.get("bar_ts", row.get("timestamp", idx))
                if hasattr(ts, "strftime"):
                    date_key = ts.strftime("%Y-%m-%d")
                else:
                    date_key = str(ts)[:10]
                actual_prices[date_key] = float(row.get("close", 0))

        # Build timestamp->price lookup from intraday data (5-min resolution)
        intraday_prices: Dict[int, float] = {}  # unix timestamp -> close price
        if df_intraday is not None and len(df_intraday) > 0:
            for idx, row in df_intraday.iterrows():
                ts = row.get("bar_ts", row.get("timestamp", idx))
                if hasattr(ts, "timestamp"):
                    unix_ts = int(ts.timestamp())
                else:
                    try:
                        unix_ts = int(datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp())
                    except Exception:
                        continue
                intraday_prices[unix_ts] = float(row.get("close", 0))

        # Enrich predictions with actual prices
        enriched = []
        total_error_pct = 0
        direction_correct = 0
        total_resolved = 0

        for entry in entries[-limit:]:
            pred_time = entry["timestamp"]
            pred_date = pred_time[:10]
            base_price = entry["current_price"]

            for horizon, pred in entry.get("predictions", {}).items():
                # Determine target date based on horizon
                pred_dt = datetime.fromisoformat(pred_time.replace("Z", "+00:00").replace("+00:00", ""))
                if horizon == "1h":
                    target_dt = pred_dt + timedelta(hours=1)
                elif horizon == "4h":
                    target_dt = pred_dt + timedelta(hours=4)
                elif horizon == "1d":
                    target_dt = pred_dt + timedelta(days=1)
                elif horizon == "1w":
                    target_dt = pred_dt + timedelta(weeks=1)
                else:
                    target_dt = pred_dt + timedelta(days=1)

                target_date = target_dt.strftime("%Y-%m-%d")
                target_timestamp = target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

                # For short horizons (1h, 4h), try intraday data first
                actual = None
                if horizon in ("1h", "4h") and intraday_prices:
                    target_unix = int(target_dt.timestamp())
                    # Find closest candle within 10-minute window
                    best_match = None
                    best_diff = 600  # 10 minutes max
                    for ts_unix, price in intraday_prices.items():
                        diff = abs(ts_unix - target_unix)
                        if diff < best_diff:
                            best_diff = diff
                            best_match = price
                    actual = best_match

                # For daily+ horizons, use daily data
                if actual is None:
                    actual = actual_prices.get(target_date)

                result_entry = {
                    "predicted_at": pred_time,
                    "horizon": horizon,
                    "base_price": base_price,
                    "predicted_price": pred["predicted_price"],
                    "confidence": pred["confidence"],
                    "direction": pred["direction"],
                    "target_date": target_date,
                    "target_timestamp": target_timestamp,
                    "actual_price": actual,
                    "error_pct": None,
                    "direction_correct": None,
                }

                if actual is not None and pred["predicted_price"]:
                    error = abs(actual - pred["predicted_price"]) / actual * 100
                    result_entry["error_pct"] = round(error, 2)
                    total_error_pct += error
                    total_resolved += 1

                    # Check directional accuracy
                    pred_direction = "UP" if pred["predicted_price"] > base_price else "DOWN"
                    actual_direction = "UP" if actual > base_price else "DOWN"
                    result_entry["direction_correct"] = pred_direction == actual_direction
                    if result_entry["direction_correct"]:
                        direction_correct += 1

                enriched.append(result_entry)

        accuracy = None
        if total_resolved > 0:
            accuracy = {
                "mape": round(total_error_pct / total_resolved, 2),
                "directional_accuracy": round(direction_correct / total_resolved * 100, 1),
                "total_predictions": len(enriched),
                "resolved": total_resolved,
            }

        return {
            "status": "success",
            "symbol": ticker,
            "count": len(enriched),
            "predictions": enriched,
            "accuracy": accuracy,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
