"""
Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Multi-Agent Stock Prediction API",
    description="API for multi-agent stock prediction system",
    version="1.0.0"
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
from api.routers import data

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

