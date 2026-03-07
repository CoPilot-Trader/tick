"""
Sentiment Analysis API Router.

Provides REST endpoints for:
- News fetching
- LLM sentiment analysis
- Sentiment aggregation
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import agents
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.llm_sentiment_agent.agent import LLMSentimentAgent
from agents.sentiment_aggregator.agent import SentimentAggregator

load_dotenv()

router = APIRouter(prefix="/api/v1/sentiment", tags=["Sentiment Analysis"])

# Global agent instances
_news_agent: Optional[NewsFetchAgent] = None
_llm_agent: Optional[LLMSentimentAgent] = None
_aggregator: Optional[SentimentAggregator] = None


def get_news_agent() -> NewsFetchAgent:
    """Get or create News Fetch Agent instance with live API keys."""
    global _news_agent
    if _news_agent is None:
        finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        newsapi_key = os.getenv("NEWSAPI_KEY", "")
        alphavantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")

        has_finnhub = bool(finnhub_key and finnhub_key.strip())
        has_newsapi = bool(newsapi_key and newsapi_key.strip())
        has_alphavantage = bool(alphavantage_key and alphavantage_key.strip())

        use_mock = not (has_finnhub or has_newsapi or has_alphavantage)

        news_config: Dict[str, Any] = {"use_mock_data": use_mock}
        if has_finnhub:
            news_config["finnhub_api_key"] = finnhub_key.strip()
        if has_newsapi:
            news_config["newsapi_key"] = newsapi_key.strip()
        if has_alphavantage:
            news_config["alpha_vantage_api_key"] = alphavantage_key.strip()

        _news_agent = NewsFetchAgent(config=news_config)
        _news_agent.initialize()
    return _news_agent


def get_llm_agent() -> LLMSentimentAgent:
    """Get or create LLM Sentiment Agent instance with live OpenAI key."""
    global _llm_agent
    if _llm_agent is None:
        openai_key = os.getenv("OPENAI_API_KEY", "")
        has_openai = bool(openai_key and openai_key.strip())

        try:
            import sentence_transformers
            use_cache = True
        except ImportError:
            use_cache = False

        llm_config: Dict[str, Any] = {
            "use_mock_data": not has_openai,
            "use_cache": use_cache,
        }
        if has_openai:
            llm_config["openai_api_key"] = openai_key.strip()

        _llm_agent = LLMSentimentAgent(config=llm_config)
        _llm_agent.initialize()
    return _llm_agent


def get_aggregator() -> SentimentAggregator:
    """Get or create Sentiment Aggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = SentimentAggregator(config={"use_time_weighting": True})
        _aggregator.initialize()
    return _aggregator


# ============================================================================
# Request/Response Models
# ============================================================================

class NewsRequest(BaseModel):
    """Request model for news fetching."""
    ticker: str = Field(..., description="Stock symbol (e.g., AAPL)")
    days: int = Field(default=7, ge=1, le=30, description="Days of news to fetch")
    max_articles: int = Field(default=20, ge=5, le=100, description="Maximum articles to fetch")


class SentimentRequest(BaseModel):
    """Request model for sentiment analysis."""
    ticker: str = Field(..., description="Stock symbol")
    days: int = Field(default=7, ge=1, le=30, description="Days of news")
    max_articles: int = Field(default=20, ge=5, le=100, description="Maximum articles")
    time_horizon: str = Field(default="1d", description="Prediction time horizon")
    use_time_weighting: bool = Field(default=True, description="Use time-weighted aggregation")


class AggregateRequest(BaseModel):
    """Request model for sentiment aggregation."""
    ticker: str = Field(..., description="Stock symbol")
    sentiment_scores: List[Dict[str, Any]] = Field(..., description="List of sentiment scores")
    time_horizon: str = Field(default="1d", description="Prediction time horizon")
    use_time_weighting: bool = Field(default=True, description="Use time-weighted aggregation")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check Sentiment Analysis system health."""
    news_agent = get_news_agent()
    llm_agent = get_llm_agent()
    aggregator = get_aggregator()

    return {
        "news_agent": news_agent.health_check(),
        "llm_sentiment_agent": llm_agent.health_check(),
        "sentiment_aggregator": aggregator.health_check()
    }


@router.get("/news/{ticker}")
async def fetch_news(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    max_articles: int = Query(20, ge=5, le=100)
) -> Dict[str, Any]:
    """
    Fetch news articles for a ticker.

    Returns filtered and deduplicated news from multiple sources.
    """
    try:
        news_agent = get_news_agent()
        result = news_agent.process(ticker, params={
            "days": days,
            "max_articles": max_articles
        })

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "News fetch failed"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}")
async def get_sentiment(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    max_articles: int = Query(20, ge=5, le=100),
    time_horizon: str = Query("1d", description="Time horizon (1h, 1d, 1w, 1mo)"),
    use_time_weighting: bool = Query(True)
) -> Dict[str, Any]:
    """
    Get full sentiment analysis for a ticker.

    Pipeline:
    1. Fetch news from multiple sources
    2. Analyze sentiment with LLM
    3. Aggregate with time weighting
    4. Return unified sentiment score

    Returns:
        Aggregated sentiment with confidence and impact.
    """
    try:
        # Step 1: Fetch news
        news_agent = get_news_agent()
        news_result = news_agent.process(ticker, params={
            "days": days,
            "max_articles": max_articles
        })

        if news_result.get("status") == "error":
            return {
                "symbol": ticker,
                "status": "error",
                "message": f"News fetch failed: {news_result.get('message')}",
                "aggregated_sentiment": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "impact": "Low",
                "news_count": 0
            }

        articles = news_result.get("articles", [])
        if not articles:
            return {
                "symbol": ticker,
                "status": "success",
                "message": "No news articles found",
                "aggregated_sentiment": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "impact": "Low",
                "news_count": 0
            }

        # Step 2: Analyze sentiment with LLM
        llm_agent = get_llm_agent()
        sentiment_scores = []

        for article in articles:
            sentiment_result = llm_agent.process(ticker, params={
                "article": article,
                "time_horizon": time_horizon
            })

            if sentiment_result.get("status") == "success":
                sentiment_scores.append({
                    "sentiment_score": sentiment_result.get("sentiment_score", 0.0),
                    "confidence": sentiment_result.get("confidence", 0.5),
                    "processed_at": sentiment_result.get("processed_at"),
                    "article": article
                })

        if not sentiment_scores:
            return {
                "symbol": ticker,
                "status": "success",
                "message": "No sentiment scores generated",
                "aggregated_sentiment": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "impact": "Low",
                "news_count": len(articles)
            }

        # Step 3: Aggregate sentiment
        aggregator = get_aggregator()
        aggregated = aggregator.process(ticker, params={
            "sentiment_scores": sentiment_scores,
            "time_weighted": use_time_weighting,
            "time_horizon": time_horizon
        })

        # Add pipeline metadata
        aggregated["pipeline"] = {
            "news_sources": news_result.get("sources_used", []),
            "total_articles_fetched": len(articles),
            "articles_analyzed": len(sentiment_scores),
            "llm_cache_stats": llm_agent.get_cache_stats() if hasattr(llm_agent, 'get_cache_stats') else {}
        }

        return aggregated

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aggregate")
async def aggregate_sentiment(request: AggregateRequest) -> Dict[str, Any]:
    """
    Aggregate sentiment scores (direct API).

    Use this endpoint to aggregate pre-computed sentiment scores.
    """
    try:
        aggregator = get_aggregator()
        result = aggregator.process(request.ticker, params={
            "sentiment_scores": request.sentiment_scores,
            "time_weighted": request.use_time_weighting,
            "time_horizon": request.time_horizon
        })
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/news-only")
async def get_news_only(
    ticker: str,
    days: int = Query(7, ge=1, le=30),
    max_articles: int = Query(20, ge=5, le=100)
) -> Dict[str, Any]:
    """
    Fetch news without sentiment analysis.

    Useful for debugging or manual analysis.
    """
    try:
        news_agent = get_news_agent()
        return news_agent.process(ticker, params={
            "days": days,
            "max_articles": max_articles
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/analyze-article")
async def analyze_single_article(
    ticker: str,
    title: str = Query(..., description="Article title"),
    content: str = Query(None, description="Article content (optional)"),
    time_horizon: str = Query("1d")
) -> Dict[str, Any]:
    """
    Analyze sentiment for a single article.

    Useful for testing or one-off analysis.
    """
    try:
        llm_agent = get_llm_agent()
        article = {
            "title": title,
            "content": content or title,
            "published_at": datetime.utcnow().isoformat() + "Z"
        }

        result = llm_agent.process(ticker, params={
            "article": article,
            "time_horizon": time_horizon
        })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get LLM sentiment cache statistics."""
    try:
        llm_agent = get_llm_agent()
        if hasattr(llm_agent, 'get_cache_stats'):
            return llm_agent.get_cache_stats()
        return {"message": "Cache stats not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(ticker: Optional[str] = None) -> Dict[str, str]:
    """Clear LLM sentiment cache."""
    try:
        llm_agent = get_llm_agent()
        if hasattr(llm_agent, 'clear_cache'):
            llm_agent.clear_cache(ticker)
        return {
            "status": "success",
            "message": f"Cache cleared for {ticker if ticker else 'all tickers'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
