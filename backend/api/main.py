"""
Main FastAPI application.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import partial

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# All tracked symbols — predictions run for every stock, every 5 minutes
AUTO_PREDICT_SYMBOLS = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "INTC",
    # ETF
    "SPY",
    # Energy
    "XOM", "CVX", "SLB", "COP", "EOG",
    # Healthcare
    "JNJ", "PFE", "UNH", "ABBV", "TMO",
    # Finance
    "JPM", "BAC", "GS", "MS", "WFC", "V",
    # Consumer
    "WMT", "PG", "KO", "PEP", "MCD",
]
PREDICTION_INTERVAL_SECONDS = 300  # 5 minutes
MAX_PARALLEL_WORKERS = 8  # Run 8 predictions at a time


def _predict_single(symbol: str) -> str:
    """Run a single prediction synchronously (called from thread pool)."""
    from api.routers.price_forecast import get_forecast_agent, get_data_agent, _store_prediction

    try:
        data_agent = get_data_agent()
        forecast_agent = get_forecast_agent()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        df = data_agent.fetch_historical_sync(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d",
        )

        if df is None or len(df) < 60:
            return f"{symbol}: skipped (insufficient data)"

        result = forecast_agent.predict(
            symbol=symbol,
            df=df,
            horizons=["1h"],
            use_baseline=True,
            use_ensemble=False,
        )

        if result.get("success") and result.get("predictions") and result.get("current_price"):
            _store_prediction(symbol, result["current_price"], result["predictions"])
            pred_1h = result["predictions"].get("1h", {}).get("price", "N/A")
            return f"{symbol}: {result['current_price']:.2f} → 1h={pred_1h}"

        return f"{symbol}: prediction failed"

    except Exception as e:
        return f"{symbol}: error ({e})"


async def _run_auto_predictions():
    """Background task: run predictions for ALL stocks every 5 minutes using parallel threads."""
    await asyncio.sleep(10)

    logger.info(
        f"Auto-prediction started: {len(AUTO_PREDICT_SYMBOLS)} symbols, "
        f"{MAX_PARALLEL_WORKERS} parallel workers, every {PREDICTION_INTERVAL_SECONDS}s"
    )

    loop = asyncio.get_event_loop()

    while True:
        t0 = time.time()
        try:
            with ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as pool:
                results = await loop.run_in_executor(
                    None,
                    lambda: list(pool.map(_predict_single, AUTO_PREDICT_SYMBOLS)),
                )

            elapsed = time.time() - t0
            ok = sum(1 for r in results if "→" in r)
            logger.info(
                f"Auto-prediction cycle complete: {ok}/{len(AUTO_PREDICT_SYMBOLS)} succeeded "
                f"in {elapsed:.1f}s"
            )

        except Exception as e:
            logger.warning(f"Auto-prediction cycle failed: {e}")

        await asyncio.sleep(PREDICTION_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on app startup, clean up on shutdown."""
    task = asyncio.create_task(_run_auto_predictions())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Multi-Agent Stock Prediction API",
    description="API for multi-agent stock prediction system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
# Allow all origins for development (including file:// for local HTML files)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Agent Stock Prediction API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include agent routers
from api.routers import news_pipeline_visualizer, support_resistance_agent
from api.routers import price_forecast, trend_classification
from api.routers import sentiment, fusion
from api.routers import backtest, alerts
from api.routers import data, streaming

app.include_router(news_pipeline_visualizer.router)
app.include_router(support_resistance_agent.router)

# M2 Prediction Agents
app.include_router(price_forecast.router)
app.include_router(trend_classification.router)

# M3 Sentiment & Fusion Agents
app.include_router(sentiment.router)
app.include_router(fusion.router)

# M4 Backtesting & Alerts
app.include_router(backtest.router)
app.include_router(alerts.router)

# Data endpoints
app.include_router(data.router)

# Real-time streaming
app.include_router(streaming.router)

