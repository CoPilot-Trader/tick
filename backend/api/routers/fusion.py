"""
Fusion Agent API Router.

Provides REST endpoints for:
- Signal fusion from all components
- Full pipeline execution
- Weight management
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import agents
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.fusion_agent.agent import FusionAgent
from agents.price_forecast_agent.agent import PriceForecastAgent
from agents.trend_classification_agent.agent import TrendClassificationAgent
from agents.support_resistance_agent.agent import SupportResistanceAgent
from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.llm_sentiment_agent.agent import LLMSentimentAgent
from agents.sentiment_aggregator.agent import SentimentAggregator
from agents.data_agent.agent import DataAgent
from agents.feature_agent.agent import FeatureAgent

router = APIRouter(prefix="/api/v1/fusion", tags=["Signal Fusion"])

# Global agent instances
_fusion_agent: Optional[FusionAgent] = None
_data_agent: Optional[DataAgent] = None
_feature_agent: Optional[FeatureAgent] = None
_price_forecast_agent: Optional[PriceForecastAgent] = None
_trend_agent: Optional[TrendClassificationAgent] = None
_sr_agent: Optional[SupportResistanceAgent] = None
_news_agent: Optional[NewsFetchAgent] = None
_llm_agent: Optional[LLMSentimentAgent] = None
_aggregator: Optional[SentimentAggregator] = None


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


def get_price_forecast_agent() -> PriceForecastAgent:
    """Get or create Price Forecast Agent instance."""
    global _price_forecast_agent
    if _price_forecast_agent is None:
        _price_forecast_agent = PriceForecastAgent()
        _price_forecast_agent.initialize()
    return _price_forecast_agent


def get_trend_agent() -> TrendClassificationAgent:
    """Get or create Trend Classification Agent instance."""
    global _trend_agent
    if _trend_agent is None:
        _trend_agent = TrendClassificationAgent()
        _trend_agent.initialize()
    return _trend_agent


def get_sr_agent() -> SupportResistanceAgent:
    """Get or create Support/Resistance Agent instance."""
    global _sr_agent
    if _sr_agent is None:
        _sr_agent = SupportResistanceAgent()
        _sr_agent.initialize()
    return _sr_agent


def get_sentiment_pipeline():
    """Get or create sentiment pipeline agents."""
    global _news_agent, _llm_agent, _aggregator

    if _news_agent is None:
        _news_agent = NewsFetchAgent()
        _news_agent.initialize()

    if _llm_agent is None:
        _llm_agent = LLMSentimentAgent()
        _llm_agent.initialize()

    if _aggregator is None:
        _aggregator = SentimentAggregator()
        _aggregator.initialize()

    return _news_agent, _llm_agent, _aggregator


# ============================================================================
# Request/Response Models
# ============================================================================

class FuseRequest(BaseModel):
    """Request model for manual signal fusion."""
    ticker: str = Field(..., description="Stock symbol")
    price_forecast: Optional[Dict[str, Any]] = Field(None, description="Price forecast output")
    trend_classification: Optional[Dict[str, Any]] = Field(None, description="Trend classification output")
    support_resistance: Optional[Dict[str, Any]] = Field(None, description="Support/Resistance output")
    sentiment: Optional[Dict[str, Any]] = Field(None, description="Aggregated sentiment output")
    current_price: Optional[float] = Field(None, description="Current stock price")
    time_horizon: str = Field(default="1d", description="Prediction time horizon")


class WeightUpdateRequest(BaseModel):
    """Request model for weight update."""
    price_forecast: float = Field(default=0.30, ge=0, le=1)
    trend_classification: float = Field(default=0.25, ge=0, le=1)
    support_resistance: float = Field(default=0.20, ge=0, le=1)
    sentiment: float = Field(default=0.25, ge=0, le=1)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Fusion Agent health."""
    fusion_agent = get_fusion_agent()
    return fusion_agent.health_check()


@router.get("/{ticker}")
async def get_fused_signal(
    ticker: str,
    days: int = Query(365, ge=100, le=1825, description="Days of price data"),
    news_days: int = Query(7, ge=1, le=30, description="Days of news data"),
    time_horizon: str = Query("1d", description="Time horizon (1h, 1d, 1w)"),
    include_components: bool = Query(True, description="Include component details")
) -> Dict[str, Any]:
    """
    Get fused trading signal for a ticker.

    This is the main endpoint that runs the full pipeline:
    1. Fetches price data
    2. Runs Price Forecast Agent
    3. Runs Trend Classification Agent
    4. Runs Support/Resistance Agent
    5. Runs Sentiment Pipeline (News → LLM → Aggregator)
    6. Fuses all signals into unified BUY/SELL/HOLD

    Returns:
        Fused signal with confidence and reasoning.
    """
    try:
        # Get agents
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()
        fusion_agent = get_fusion_agent()

        # Fetch price data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d"
        )

        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}. Need at least 100 data points."
            )

        # Get current price
        current_price = float(df['close'].iloc[-1])

        # Calculate features
        df_with_features = feature_agent.calculate_all(df)

        # Run component agents in sequence
        component_results = {}
        component_errors = []

        # 1. Price Forecast
        try:
            price_agent = get_price_forecast_agent()
            price_result = price_agent.forecast(
                symbol=ticker,
                df=df_with_features,
                timeframe="1d",
                horizon=5
            )
            component_results["price_forecast"] = price_result
        except Exception as e:
            component_errors.append(f"Price Forecast: {str(e)}")
            component_results["price_forecast"] = {"status": "error", "message": str(e)}

        # 2. Trend Classification
        try:
            trend_agent = get_trend_agent()
            trend_result = trend_agent.classify(
                symbol=ticker,
                df=df_with_features,
                timeframe="1d"
            )
            component_results["trend_classification"] = trend_result
        except Exception as e:
            component_errors.append(f"Trend Classification: {str(e)}")
            component_results["trend_classification"] = {"success": False, "error": str(e)}

        # 3. Support/Resistance
        try:
            sr_agent = get_sr_agent()
            sr_result = sr_agent.process(ticker, params={
                "df": df_with_features,
                "current_price": current_price
            })
            component_results["support_resistance"] = sr_result
        except Exception as e:
            component_errors.append(f"Support/Resistance: {str(e)}")
            component_results["support_resistance"] = {"status": "error", "message": str(e)}

        # 4. Sentiment Pipeline
        try:
            news_agent, llm_agent, aggregator = get_sentiment_pipeline()

            # Fetch news
            news_result = news_agent.process(ticker, params={
                "days": news_days,
                "max_articles": 20
            })

            if news_result.get("status") == "success" and news_result.get("articles"):
                # Analyze sentiment
                sentiment_scores = []
                for article in news_result.get("articles", [])[:15]:  # Limit to 15 for speed
                    sent_result = llm_agent.process(ticker, params={
                        "article": article,
                        "time_horizon": time_horizon
                    })
                    if sent_result.get("status") == "success":
                        sentiment_scores.append({
                            "sentiment_score": sent_result.get("sentiment_score", 0.0),
                            "confidence": sent_result.get("confidence", 0.5),
                            "processed_at": sent_result.get("processed_at")
                        })

                # Aggregate
                if sentiment_scores:
                    agg_result = aggregator.process(ticker, params={
                        "sentiment_scores": sentiment_scores,
                        "time_weighted": True,
                        "time_horizon": time_horizon
                    })
                    component_results["sentiment"] = agg_result
                else:
                    component_results["sentiment"] = {
                        "status": "success",
                        "aggregated_sentiment": 0.0,
                        "confidence": 0.0,
                        "impact": "Low"
                    }
            else:
                component_results["sentiment"] = {
                    "status": "success",
                    "aggregated_sentiment": 0.0,
                    "confidence": 0.0,
                    "impact": "Low",
                    "message": "No news available"
                }
        except Exception as e:
            component_errors.append(f"Sentiment: {str(e)}")
            component_results["sentiment"] = {"status": "error", "message": str(e)}

        # 5. Fuse signals
        fused_result = fusion_agent.fuse_signals(
            price_forecast=component_results.get("price_forecast", {}),
            trend_classification=component_results.get("trend_classification", {}),
            support_resistance=component_results.get("support_resistance", {}),
            sentiment=component_results.get("sentiment", {}),
            symbol=ticker,
            current_price=current_price
        )

        # Add metadata
        fused_result["current_price"] = current_price
        fused_result["data_points"] = len(df)

        if component_errors:
            fused_result["component_errors"] = component_errors

        if include_components:
            fused_result["component_results"] = component_results

        return fused_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fuse")
async def fuse_signals(request: FuseRequest) -> Dict[str, Any]:
    """
    Manually fuse pre-computed component signals.

    Use this endpoint when you have already computed individual
    component outputs and want to fuse them.
    """
    try:
        fusion_agent = get_fusion_agent()
        result = fusion_agent.fuse_signals(
            price_forecast=request.price_forecast or {},
            trend_classification=request.trend_classification or {},
            support_resistance=request.support_resistance or {},
            sentiment=request.sentiment or {},
            symbol=request.ticker,
            current_price=request.current_price
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/quick")
async def get_quick_signal(
    ticker: str,
    days: int = Query(180, ge=100, le=365),
    time_horizon: str = Query("1d")
) -> Dict[str, Any]:
    """
    Get quick fused signal (minimal news analysis).

    Faster version that skips sentiment for speed.
    """
    try:
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()
        fusion_agent = get_fusion_agent()

        # Fetch price data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d"
        )

        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}"
            )

        current_price = float(df['close'].iloc[-1])
        df_with_features = feature_agent.calculate_all(df)

        # Run only technical agents
        component_results = {}

        # Price Forecast
        try:
            price_agent = get_price_forecast_agent()
            component_results["price_forecast"] = price_agent.forecast(
                symbol=ticker, df=df_with_features, timeframe="1d", horizon=5
            )
        except:
            component_results["price_forecast"] = {}

        # Trend Classification
        try:
            trend_agent = get_trend_agent()
            component_results["trend_classification"] = trend_agent.classify(
                symbol=ticker, df=df_with_features, timeframe="1d"
            )
        except:
            component_results["trend_classification"] = {}

        # Support/Resistance
        try:
            sr_agent = get_sr_agent()
            component_results["support_resistance"] = sr_agent.process(ticker, params={
                "df": df_with_features, "current_price": current_price
            })
        except:
            component_results["support_resistance"] = {}

        # Fuse without sentiment
        result = fusion_agent.fuse_signals(
            price_forecast=component_results.get("price_forecast", {}),
            trend_classification=component_results.get("trend_classification", {}),
            support_resistance=component_results.get("support_resistance", {}),
            sentiment={},  # Skip sentiment for speed
            symbol=ticker,
            current_price=current_price
        )

        result["mode"] = "quick"
        result["current_price"] = current_price
        result["note"] = "Sentiment analysis skipped for speed"

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights")
async def get_weights() -> Dict[str, float]:
    """Get current component weights."""
    fusion_agent = get_fusion_agent()
    return fusion_agent.component_weights


@router.put("/weights")
async def update_weights(request: WeightUpdateRequest) -> Dict[str, Any]:
    """Update component weights."""
    try:
        fusion_agent = get_fusion_agent()
        new_weights = {
            "price_forecast": request.price_forecast,
            "trend_classification": request.trend_classification,
            "support_resistance": request.support_resistance,
            "sentiment": request.sentiment
        }

        success = fusion_agent.update_weights(new_weights)
        if success:
            return {
                "status": "success",
                "message": "Weights updated",
                "weights": fusion_agent.component_weights
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update weights")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/status")
async def get_component_status() -> Dict[str, Any]:
    """Get health status of all component agents."""
    try:
        statuses = {}

        # Fusion Agent
        statuses["fusion_agent"] = get_fusion_agent().health_check()

        # Price Forecast
        try:
            statuses["price_forecast_agent"] = get_price_forecast_agent().health_check()
        except Exception as e:
            statuses["price_forecast_agent"] = {"status": "error", "message": str(e)}

        # Trend Classification
        try:
            statuses["trend_classification_agent"] = get_trend_agent().health_check()
        except Exception as e:
            statuses["trend_classification_agent"] = {"status": "error", "message": str(e)}

        # Support/Resistance
        try:
            statuses["support_resistance_agent"] = get_sr_agent().health_check()
        except Exception as e:
            statuses["support_resistance_agent"] = {"status": "error", "message": str(e)}

        # Sentiment Pipeline
        try:
            news_agent, llm_agent, aggregator = get_sentiment_pipeline()
            statuses["news_fetch_agent"] = news_agent.health_check()
            statuses["llm_sentiment_agent"] = llm_agent.health_check()
            statuses["sentiment_aggregator"] = aggregator.health_check()
        except Exception as e:
            statuses["sentiment_pipeline"] = {"status": "error", "message": str(e)}

        return statuses

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/multi-timeframe")
async def get_multi_timeframe_signal(
    ticker: str,
    days: int = Query(365, ge=100, le=1825),
) -> Dict[str, Any]:
    """
    Get trading signals across multiple timeframes (1h and 1d).

    Returns independent fusion signals for each timeframe so traders
    can see whether short-term and long-term views agree or conflict.
    """
    try:
        data_agent = get_data_agent()
        feature_agent = get_feature_agent()
        fusion_agent = get_fusion_agent()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = data_agent.fetch_historical_sync(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1d",
        )

        if df is None or len(df) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker}",
            )

        current_price = float(df["close"].iloc[-1])
        df_with_features = feature_agent.calculate_all(df)

        timeframe_results: Dict[str, Any] = {}

        for tf in ["1h", "1d"]:
            components: Dict[str, Any] = {}

            # Trend Classification
            try:
                trend_agent = get_trend_agent()
                components["trend_classification"] = trend_agent.classify(
                    symbol=ticker, df=df_with_features, timeframe=tf
                )
            except Exception:
                components["trend_classification"] = {}

            # Price Forecast
            try:
                price_agent = get_price_forecast_agent()
                components["price_forecast"] = price_agent.forecast(
                    symbol=ticker, df=df_with_features, timeframe=tf, horizon=5
                )
            except Exception:
                components["price_forecast"] = {}

            # Support/Resistance (same for all timeframes)
            try:
                sr_agent = get_sr_agent()
                components["support_resistance"] = sr_agent.process(
                    ticker, params={"df": df_with_features, "current_price": current_price}
                )
            except Exception:
                components["support_resistance"] = {}

            # Fuse
            fused = fusion_agent.fuse_signals(
                price_forecast=components.get("price_forecast", {}),
                trend_classification=components.get("trend_classification", {}),
                support_resistance=components.get("support_resistance", {}),
                sentiment={},
                symbol=ticker,
                current_price=current_price,
            )

            timeframe_results[tf] = {
                "signal": fused.get("signal", "HOLD"),
                "confidence": fused.get("confidence", 0.0),
                "fused_score": fused.get("fused_score", 0.0),
                "reasoning": fused.get("reasoning", ""),
                "components": fused.get("components", {}),
            }

        # Determine agreement
        signals = [v["signal"] for v in timeframe_results.values()]
        agreement = "ALIGNED" if len(set(signals)) == 1 else "CONFLICTING"

        return {
            "status": "success",
            "symbol": ticker,
            "current_price": current_price,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "timeframes": timeframe_results,
            "agreement": agreement,
            "consensus_signal": signals[0] if agreement == "ALIGNED" else "HOLD",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
