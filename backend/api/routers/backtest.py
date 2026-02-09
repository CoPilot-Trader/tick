"""
Backtesting API Router.

Provides REST endpoints for:
- Running backtests
- Walk-forward testing
- Performance metrics
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


def _sanitize(obj):
    """Convert numpy/pandas types to Python native for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    if hasattr(obj, 'item'):
        return obj.item()
    return obj

# Import agents
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.backtesting_agent.agent import BacktestingAgent
from agents.fusion_agent.agent import FusionAgent
from agents.data_agent.agent import DataAgent
from agents.feature_agent.agent import FeatureAgent

router = APIRouter(prefix="/api/v1/backtest", tags=["Backtesting"])

# Global agent instances
_backtest_agent: Optional[BacktestingAgent] = None
_fusion_agent: Optional[FusionAgent] = None
_data_agent: Optional[DataAgent] = None
_feature_agent: Optional[FeatureAgent] = None


def get_backtest_agent() -> BacktestingAgent:
    """Get or create Backtesting Agent instance."""
    global _backtest_agent
    if _backtest_agent is None:
        _backtest_agent = BacktestingAgent()
        _backtest_agent.initialize()
    return _backtest_agent


def get_fusion_agent() -> FusionAgent:
    """Get or create Fusion Agent instance."""
    global _fusion_agent
    if _fusion_agent is None:
        _fusion_agent = FusionAgent()
        _fusion_agent.initialize()
    return _fusion_agent


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

class BacktestRequest(BaseModel):
    """Request model for backtest."""
    ticker: str = Field(..., description="Stock symbol")
    days: int = Field(default=365, ge=60, le=1825, description="Days of historical data")
    initial_capital: float = Field(default=100000, ge=1000, description="Starting capital")
    stop_loss_pct: float = Field(default=0.05, ge=0.01, le=0.20, description="Stop loss percentage")
    take_profit_pct: float = Field(default=0.10, ge=0.02, le=0.50, description="Take profit percentage")


class WalkForwardRequest(BaseModel):
    """Request model for walk-forward backtest."""
    ticker: str = Field(..., description="Stock symbol")
    days: int = Field(default=730, ge=365, le=3650, description="Total days of data")
    train_days: int = Field(default=252, ge=60, description="Training period days")
    test_days: int = Field(default=63, ge=21, description="Testing period days")
    step_days: int = Field(default=21, ge=5, description="Step forward days")


class ConfigUpdateRequest(BaseModel):
    """Request model for config update."""
    initial_capital: Optional[float] = None
    max_position_size: Optional[float] = None
    commission_rate: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    min_confidence: Optional[float] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Backtesting Agent health."""
    agent = get_backtest_agent()
    return agent.health_check()


@router.post("/{ticker}")
async def run_backtest(ticker: str, request: BacktestRequest) -> Dict[str, Any]:
    """
    Run backtest for a ticker.

    Uses the Fusion Agent to generate historical signals,
    then simulates trading based on those signals.

    Returns:
        Backtest results with trades and metrics.
    """
    try:
        # Get agents
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()
        fusion_agent = get_fusion_agent()
        backtest_agent = get_backtest_agent()

        # Update config if needed
        backtest_agent.update_config({
            "initial_capital": request.initial_capital,
            "stop_loss_pct": request.stop_loss_pct,
            "take_profit_pct": request.take_profit_pct
        })

        # Fetch historical data
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
                detail=f"Insufficient data for {ticker}. Need at least 60 data points."
            )

        # Use actual data date range (for mock data compatibility)
        actual_start_date = df.index.min()
        actual_end_date = df.index.max()

        # Calculate features
        df_with_features = feature_agent.calculate_all(df)

        # Generate signals for each day (simplified - using trend classification only)
        signals = []
        from agents.trend_classification_agent.agent import TrendClassificationAgent
        trend_agent = TrendClassificationAgent()
        trend_agent.initialize()

        # Generate signals for backtest period
        for i in range(60, len(df_with_features)):
            date = df_with_features.iloc[i].get('timestamp', df_with_features.index[i])
            subset = df_with_features.iloc[:i+1]

            try:
                result = trend_agent.classify(
                    symbol=ticker,
                    df=subset,
                    timeframe="1d"
                )

                signals.append({
                    "date": date,
                    "signal": result.get("signal", "HOLD"),
                    "confidence": result.get("confidence", 0.5),
                    "fused_score": 0.5 if result.get("signal") == "BUY" else (-0.5 if result.get("signal") == "SELL" else 0.0)
                })
            except:
                signals.append({
                    "date": date,
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "fused_score": 0.0
                })

        # Run backtest (use actual data date range for mock data compatibility)
        result = backtest_agent.run_backtest(
            symbol=ticker,
            price_data=df_with_features,
            signals=signals,
            start_date=actual_start_date,
            end_date=actual_end_date
        )

        # Add summary
        if result.get("status") == "success":
            result["summary"] = {
                "ticker": ticker,
                "period": f"{request.days} days",
                "initial_capital": request.initial_capital,
                "final_equity": result.get("final_equity"),
                "total_return_pct": result.get("total_return"),
                "total_trades": result.get("total_trades")
            }

        return JSONResponse(content=_sanitize(result))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/quick")
async def quick_backtest(
    ticker: str,
    days: int = Query(180, ge=60, le=730),
    initial_capital: float = Query(100000, ge=1000)
) -> Dict[str, Any]:
    """
    Run quick backtest with default settings.

    Simplified version for fast results.
    """
    request = BacktestRequest(
        ticker=ticker,
        days=days,
        initial_capital=initial_capital
    )
    return await run_backtest(ticker, request)


@router.post("/{ticker}/walk-forward")
async def run_walk_forward(ticker: str, request: WalkForwardRequest) -> Dict[str, Any]:
    """
    Run walk-forward backtest.

    Walk-forward testing trains models on historical data,
    tests on out-of-sample data, and repeats by stepping forward.

    Returns:
        Walk-forward results with iteration metrics.
    """
    try:
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()
        backtest_agent = get_backtest_agent()

        # Fetch historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d"
        )

        if df is None or len(df) < request.train_days + request.test_days:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for walk-forward test. Need at least {request.train_days + request.test_days} days."
            )

        df_with_features = feature_agent.calculate_all(df)

        # Define signal generator
        def generate_signals(symbol: str, train_data) -> List[Dict[str, Any]]:
            """Generate signals based on training data."""
            signals = []
            # Use simple trend following based on recent returns
            for i in range(len(train_data)):
                date = train_data.iloc[i].get('timestamp', train_data.index[i])
                if i < 10:
                    signals.append({"date": date, "signal": "HOLD", "confidence": 0.0, "fused_score": 0.0})
                    continue

                # Simple momentum: compare current price to 10-day average
                close = train_data.iloc[i].get('close', 0)
                avg = train_data.iloc[i-10:i]['close'].mean()

                if close > avg * 1.02:
                    signal = "BUY"
                    fused_score = 0.5
                elif close < avg * 0.98:
                    signal = "SELL"
                    fused_score = -0.5
                else:
                    signal = "HOLD"
                    fused_score = 0.0

                signals.append({
                    "date": date,
                    "signal": signal,
                    "confidence": 0.6,
                    "fused_score": fused_score
                })

            return signals

        # Run walk-forward
        result = backtest_agent.walk_forward_backtest(
            symbol=ticker,
            price_data=df_with_features,
            signal_generator=generate_signals,
            train_days=request.train_days,
            test_days=request.test_days,
            step_days=request.step_days
        )

        return JSONResponse(content=_sanitize(result))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current backtest configuration."""
    agent = get_backtest_agent()
    return agent.get_config()


@router.put("/config")
async def update_config(request: ConfigUpdateRequest) -> Dict[str, Any]:
    """Update backtest configuration."""
    try:
        agent = get_backtest_agent()
        updates = {k: v for k, v in request.dict().items() if v is not None}

        if updates:
            agent.update_config(updates)

        return {
            "status": "success",
            "message": "Configuration updated",
            "config": agent.get_config()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics")
async def calculate_metrics(
    trades: List[Dict[str, Any]],
    equity_curve: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate performance metrics from trade data.

    Use this endpoint to calculate metrics from external data.
    """
    try:
        agent = get_backtest_agent()
        return agent.calculate_metrics(
            trades=trades,
            equity_curve=equity_curve
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
