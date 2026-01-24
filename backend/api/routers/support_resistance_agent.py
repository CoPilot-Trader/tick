"""
API Router for Support/Resistance Agent

This endpoint provides support and resistance level detection for stocks.

Developer: Developer 2
Purpose: Expose Support/Resistance Agent via REST API
"""

import time
import traceback
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

# Import agent
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.support_resistance_agent.agent import SupportResistanceAgent

router = APIRouter(prefix="/api/v1/levels", tags=["support-resistance"])


# Request models
class LevelDetectionRequest(BaseModel):
    """Request model for level detection."""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    min_strength: int = Field(50, ge=0, le=100, description="Minimum strength score (0-100)")
    max_levels: int = Field(5, ge=1, le=20, description="Maximum levels per type (support/resistance)")
    timeframe: str = Field("1d", description="Data timeframe: 1m, 1h, 1d, 1w, 1mo, 1y")
    project_future: bool = Field(False, description="Predict future levels")
    projection_periods: int = Field(20, ge=1, le=100, description="Number of periods to project ahead")
    lookback_days: Optional[int] = Field(None, ge=1, le=3650, description="Custom lookback period in days (overrides default based on timeframe)")


class BatchLevelDetectionRequest(BaseModel):
    """Request model for batch level detection."""
    symbols: List[str] = Field(..., description="List of stock symbols")
    min_strength: int = Field(50, ge=0, le=100, description="Minimum strength score (0-100)")
    max_levels: int = Field(5, ge=1, le=20, description="Maximum levels per type")
    timeframe: str = Field("1d", description="Data timeframe: 1m, 1h, 1d, 1w, 1mo, 1y")
    project_future: bool = Field(False, description="Predict future levels")
    projection_periods: int = Field(20, ge=1, le=100, description="Number of periods to project ahead")
    lookback_days: Optional[int] = Field(None, ge=1, le=3650, description="Custom lookback period in days (overrides default based on timeframe)")
    use_parallel: bool = Field(False, description="Use parallel processing for batch")


# Initialize agent (singleton pattern)
_agent: Optional[SupportResistanceAgent] = None


def _get_agent() -> SupportResistanceAgent:
    """Initialize and return the Support/Resistance Agent."""
    global _agent
    
    if _agent is None:
        # Configure agent: use real data (yfinance) first, mock data as fallback
        config = {
            "use_mock_data": True,  # Enable mock data as fallback only
            "enable_cache": True,
            "min_strength": 50,
            "max_levels": 5
        }
        
        _agent = SupportResistanceAgent(config=config)
        initialized = _agent.initialize()
        
        if not initialized:
            raise RuntimeError(
                "Failed to initialize SupportResistanceAgent. "
                "Check logs for details."
            )
        
        if not _agent.initialized:
            raise RuntimeError(
                "SupportResistanceAgent initialization completed but agent.initialized is False. "
                "This indicates an initialization error."
            )
    
    # Double-check agent is initialized before returning
    if not _agent.initialized:
        # Try to re-initialize
        _agent.initialize()
        if not _agent.initialized:
            raise RuntimeError(
                "SupportResistanceAgent is not initialized. "
                "Please check the backend logs for initialization errors."
            )
    
    return _agent


@router.get("/{symbol}")
async def get_levels(
    symbol: str,
    min_strength: int = Query(50, ge=0, le=100, description="Minimum strength score (0-100)"),
    max_levels: int = Query(5, ge=1, le=20, description="Maximum levels per type"),
    timeframe: str = Query("1d", description="Data timeframe: 1m, 1h, 1d, 1w, 1mo, 1y"),
    project_future: bool = Query(False, description="Predict future levels"),
    projection_periods: int = Query(20, ge=1, le=100, description="Number of periods to project ahead"),
    lookback_days: Optional[int] = Query(None, ge=1, le=3650, description="Custom lookback period in days (optional, overrides default based on timeframe)")
) -> Dict[str, Any]:
    """
    Get support and resistance levels for a single symbol.
    
    Args:
        symbol: Stock symbol (e.g., AAPL)
        min_strength: Minimum strength score (0-100), default: 50
        max_levels: Maximum levels per type, default: 5
        timeframe: Data timeframe (1m, 1h, 1d, 1w, 1mo, 1y), default: 1d
        project_future: Predict future levels, default: False
        projection_periods: Number of periods ahead to project, default: 20
        lookback_days: Custom lookback period in days (optional, overrides default based on timeframe)
    
    Returns:
        Dictionary with support/resistance levels and optionally predicted future levels
    """
    start_time = time.time()
    symbol = symbol.upper()
    
    # Validate timeframe
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo", "1y"]
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    try:
        agent = _get_agent()
        
        # Process with parameters
        params = {
            "min_strength": min_strength,
            "max_levels": max_levels,
            "use_cache": True,
            "timeframe": timeframe,
            "project_future": project_future,
            "projection_periods": projection_periods
        }
        
        # Add lookback_days if provided
        if lookback_days is not None:
            params["lookback_days"] = lookback_days
        
        result = agent.process(symbol, params)
        
        # Add API metadata
        result["api_metadata"] = {
            "endpoint": f"/api/v1/levels/{symbol}",
            "request_time": datetime.utcnow().isoformat() + "Z",
            "processing_time_seconds": round(time.time() - start_time, 3)
        }
        
        # Ensure all datetime objects are converted to strings for JSON serialization
        # FastAPI's JSON encoder may not handle datetime objects properly
        # Use json.dumps/loads as a reliable way to convert all non-serializable objects
        import json
        try:
            # This will convert all datetime objects to strings via default=str
            result_json = json.dumps(result, default=str)
            result = json.loads(result_json)
        except Exception as e:
            # If that fails, try recursive conversion
            def convert_datetime(obj):
                """Recursively convert datetime objects to ISO format strings."""
                if isinstance(obj, datetime):
                    return obj.isoformat() + "Z" if obj.tzinfo else obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                elif hasattr(obj, 'to_pydatetime'):  # pandas Timestamp
                    dt = obj.to_pydatetime()
                    return dt.isoformat() + "Z" if dt.tzinfo else dt.isoformat()
                return obj
            result = convert_datetime(result)
        
        return result
        
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "symbol": symbol,
                "trace": error_trace
            }
        )


@router.post("/detect")
async def detect_levels(request: LevelDetectionRequest) -> Dict[str, Any]:
    """
    Detect support and resistance levels for a symbol.
    
    Args:
        request: LevelDetectionRequest with symbol and parameters
    
    Returns:
        Dictionary with detected levels
    """
    start_time = time.time()
    symbol = request.symbol.upper()
    
    try:
        agent = _get_agent()
        
        # Validate timeframe
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo", "1y"]
        if request.timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Process with parameters
        params = {
            "min_strength": request.min_strength,
            "max_levels": request.max_levels,
            "use_cache": True,
            "timeframe": request.timeframe,
            "project_future": request.project_future,
            "projection_periods": request.projection_periods
        }
        
        # Add lookback_days if provided
        if request.lookback_days is not None:
            params["lookback_days"] = request.lookback_days
        
        result = agent.process(symbol, params)
        
        # Add API metadata
        result["api_metadata"] = {
            "endpoint": "/api/v1/levels/detect",
            "request_time": datetime.utcnow().isoformat() + "Z",
            "processing_time_seconds": round(time.time() - start_time, 3)
        }
        
        return result
        
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "symbol": symbol,
                "trace": error_trace
            }
        )


@router.post("/batch")
async def detect_levels_batch(request: BatchLevelDetectionRequest) -> Dict[str, Any]:
    """
    Detect support and resistance levels for multiple symbols in batch.
    
    Args:
        request: BatchLevelDetectionRequest with list of symbols and parameters
    
    Returns:
        Dictionary with results for each symbol
    """
    start_time = time.time()
    symbols = [s.upper() for s in request.symbols]
    
    try:
        agent = _get_agent()
        
        # Validate timeframe
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo", "1y"]
        if request.timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Process batch - need to call process() for each symbol with new params
        results = {}
        for symbol in symbols:
            params = {
                "min_strength": request.min_strength,
                "max_levels": request.max_levels,
                "use_cache": True,
                "timeframe": request.timeframe,
                "project_future": request.project_future,
                "projection_periods": request.projection_periods
            }
            
            # Add lookback_days if provided
            if request.lookback_days is not None:
                params["lookback_days"] = request.lookback_days
            
            results[symbol] = agent.process(symbol, params)
        
        # Add API metadata
        response = {
            "results": results,
            "api_metadata": {
                "endpoint": "/api/v1/levels/batch",
                "request_time": datetime.utcnow().isoformat() + "Z",
                "processing_time_seconds": round(time.time() - start_time, 3),
                "symbols_processed": len(symbols),
                "use_parallel": request.use_parallel
            }
        }
        
        return response
        
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "symbols": symbols,
                "trace": error_trace
            }
        )


@router.get("/{symbol}/nearest")
async def get_nearest_levels(
    symbol: str,
    min_strength: int = Query(50, ge=0, le=100, description="Minimum strength score (0-100)")
) -> Dict[str, Any]:
    """
    Get the nearest support and resistance levels for a symbol.
    
    Args:
        symbol: Stock symbol (e.g., AAPL)
        min_strength: Minimum strength score (0-100), default: 50
    
    Returns:
        Dictionary with nearest support and resistance levels
    """
    start_time = time.time()
    symbol = symbol.upper()
    
    try:
        agent = _get_agent()
        
        # Process with parameters
        params = {
            "min_strength": min_strength,
            "max_levels": 1,  # Only need nearest
            "use_cache": True
        }
        
        result = agent.process(symbol, params)
        
        # Extract nearest levels
        nearest_support = result.get("nearest_support")
        nearest_resistance = result.get("nearest_resistance")
        current_price = result.get("current_price")
        
        response = {
            "symbol": symbol,
            "current_price": current_price,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "api_metadata": {
                "endpoint": f"/api/v1/levels/{symbol}/nearest",
                "request_time": datetime.utcnow().isoformat() + "Z",
                "processing_time_seconds": round(time.time() - start_time, 3)
            }
        }
        
        return response
        
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "symbol": symbol,
                "trace": error_trace
            }
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for the Support/Resistance Agent endpoint."""
    try:
        agent = _get_agent()
        health = agent.health_check()
        
        return {
            "status": "healthy",
            "agent_status": health.get("status", "unknown"),
            "agent_initialized": agent.initialized,
            "cache_size": health.get("cache_size", 0),
            "components_initialized": health.get("components_initialized", {})
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
