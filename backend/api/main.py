"""
Main FastAPI application.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Symbols to auto-predict
AUTO_PREDICT_SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOGL", "SPY"]
PREDICTION_INTERVAL_SECONDS = 300  # 5 minutes


async def _run_auto_predictions():
    """Background task: run predictions every 5 minutes and log them."""
    # Wait a bit for app to fully start
    await asyncio.sleep(10)

    # Lazy imports inside the task to avoid circular imports
    from api.routers.price_forecast import get_forecast_agent, get_data_agent, _store_prediction

    logger.info(f"Auto-prediction started for {AUTO_PREDICT_SYMBOLS} every {PREDICTION_INTERVAL_SECONDS}s")

    while True:
        for symbol in AUTO_PREDICT_SYMBOLS:
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
                    continue

                result = forecast_agent.predict(
                    symbol=symbol,
                    df=df,
                    horizons=["1h"],
                    use_baseline=True,
                    use_ensemble=False,
                )

                if result.get("success") and result.get("predictions") and result.get("current_price"):
                    _store_prediction(symbol, result["current_price"], result["predictions"])
                    logger.info(
                        f"Auto-predicted {symbol}: price={result['current_price']:.2f}, "
                        f"1h={result['predictions'].get('1h', {}).get('price', 'N/A')}"
                    )

            except Exception as e:
                logger.warning(f"Auto-prediction failed for {symbol}: {e}")

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

