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
from api.routers import news_pipeline_visualizer
app.include_router(news_pipeline_visualizer.router)

# TODO: Import and include other agent routers
# from api.routers import news_agent, price_prediction_agent
# app.include_router(news_agent.router, prefix="/api/v1/news", tags=["news"])
# app.include_router(price_prediction_agent.router, prefix="/api/v1/predictions", tags=["predictions"])

