"""
API Router for News Pipeline Visualization

This endpoint provides detailed step-by-step visualization data
for the News & Sentiment Agents pipeline.

Developer: Developer 1
Purpose: Internal visualization tool
"""

import time
import traceback
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

# Import agents
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.llm_sentiment_agent.agent import LLMSentimentAgent
from agents.sentiment_aggregator.agent import SentimentAggregator

router = APIRouter(prefix="/api/v1/news-pipeline", tags=["news-pipeline-visualizer"])


# Request model
class PipelineRequest(BaseModel):
    symbol: str
    min_relevance: float = 0.3
    max_articles: int = 10
    time_horizon: str = "1d"  # Prediction time horizon: "1s", "1m", "1h", "1d", "1w", "1mo", "1y"


# Initialize agents (singleton pattern)
_news_agent: Optional[NewsFetchAgent] = None
_llm_agent: Optional[LLMSentimentAgent] = None
_aggregator_agent: Optional[SentimentAggregator] = None


def _get_agents():
    """Initialize and return all agents."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    global _news_agent, _llm_agent, _aggregator_agent
    
    if _news_agent is None:
        # Configure news agent: use real APIs if keys are available, otherwise use mock
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        newsapi_key = os.getenv("NEWSAPI_KEY")
        alphavantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        
        # Check if keys are non-empty strings (not None and not empty after stripping)
        has_finnhub = finnhub_key and finnhub_key.strip()
        has_newsapi = newsapi_key and newsapi_key.strip()
        has_alphavantage = alphavantage_key and alphavantage_key.strip()
        
        use_mock_data = not (has_finnhub or has_newsapi or has_alphavantage)
        
        # Only pass non-empty keys to config
        news_config = {
            "use_mock_data": use_mock_data,
        }
        if has_finnhub:
            news_config["finnhub_api_key"] = finnhub_key.strip()
        if has_newsapi:
            news_config["newsapi_key"] = newsapi_key.strip()
        if has_alphavantage:
            news_config["alpha_vantage_api_key"] = alphavantage_key.strip()
        
        print(f"[News Agent] Initializing with: use_mock_data={use_mock_data}, "
              f"finnhub={'[OK]' if has_finnhub else '[NO]'}, "
              f"newsapi={'[OK]' if has_newsapi else '[NO]'}, "
              f"alphavantage={'[OK]' if has_alphavantage else '[NO]'}")
        
        _news_agent = NewsFetchAgent(config=news_config)
        _news_agent.initialize()
        
        # Log which collectors were initialized
        collector_names = [c.get_source_name() for c in _news_agent.collectors]
        print(f"[News Agent] Initialized collectors: {', '.join(collector_names)}")
    
        if _llm_agent is None:
            # Try to enable cache, but disable if sentence-transformers is not available
            try:
                import sentence_transformers
                use_cache = True
            except ImportError:
                use_cache = False
            _llm_agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": use_cache})
            _llm_agent.initialize()
    
    if _aggregator_agent is None:
        _aggregator_agent = SentimentAggregator(config={"use_time_weighting": True})
        _aggregator_agent.initialize()
    
    return _news_agent, _llm_agent, _aggregator_agent


@router.post("/visualize")
async def visualize_pipeline(request: PipelineRequest) -> Dict[str, Any]:
    """
    Run the complete news pipeline and return detailed step-by-step data.
    
    Args:
        request: PipelineRequest with symbol, min_relevance, and max_articles
    
    Returns:
        Detailed pipeline execution data with all steps
    """
    start_time = time.time()
    symbol = request.symbol.upper()
    min_relevance = request.min_relevance
    max_articles = request.max_articles
    time_horizon = request.time_horizon.lower().strip()  # Normalize time horizon
    
    try:
        # Get initialized agents
        news_agent, llm_agent, aggregator_agent = _get_agents()
        
        # Initialize response structure
        response = {
            "input": {
                "symbol": symbol,
                "min_relevance": min_relevance,
                "max_articles": max_articles,
                "time_horizon": time_horizon,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "steps": [],
            "final_result": None,
            "total_duration_ms": 0,
            "status": "success"
        }
        
        # ============================================
        # STEP 1: News Fetch Agent
        # ============================================
        step1_start = time.time()
        step1_data = {
            "agent": "news_fetch_agent",
            "status": "processing",
            "start_time": datetime.utcnow().isoformat() + "Z",
            "details": {}
        }
        
        try:
            # Process news fetch with actual filtering
            news_params = {
                "limit": max_articles,
                "min_relevance": min_relevance,
                "time_horizon": time_horizon  # Pass time horizon
            }
            news_result = news_agent.process(symbol, news_params)
            
            step1_duration = (time.time() - step1_start) * 1000
            
            # Extract detailed information
            articles = news_result.get("articles", [])
            
            # Ensure articles are in dict format (not Pydantic models)
            articles = [
                article if isinstance(article, dict) 
                else article.dict() if hasattr(article, 'dict') 
                else dict(article) 
                for article in articles
            ]
            
            # Get raw count from agent response (before filtering)
            raw_articles_count = news_result.get("raw_articles_count", len(articles))
            
            step1_data.update({
                "status": "completed" if news_result.get("status") == "success" else "error",
                "duration_ms": round(step1_duration, 2),
                "details": {
                    "raw_articles_count": raw_articles_count,  # Raw count from agent (before filtering)
                    "final_articles_count": len(articles),  # After filtering
                    "sources_used": news_result.get("sources", []),
                    "data_source": news_result.get("data_source", "unknown"),  # "api" or "mock"
                    "api_usage": news_result.get("api_usage", []),  # API usage info
                    "final_articles": articles[:max_articles],  # Limit for display
                    "total_available": news_result.get("total_count", 0),
                    "fetched_at": news_result.get("fetched_at"),
                    "message": news_result.get("message", "Success")
                }
            })
            
        except Exception as e:
            step1_data.update({
                "status": "error",
                "duration_ms": round((time.time() - step1_start) * 1000, 2),
                "error": str(e)
            })
            response["steps"].append(step1_data)
            response["status"] = "error"
            response["error"] = f"News Fetch Agent failed: {str(e)}"
            response["total_duration_ms"] = round((time.time() - start_time) * 1000, 2)
            return response
        
        response["steps"].append(step1_data)
        
        # Continue to Steps 2 and 3 even if no articles (for visualization)
        # ============================================
        # STEP 2: LLM Sentiment Agent
        # ============================================
        step2_start = time.time()
        step2_data = {
            "agent": "llm_sentiment_agent",
            "status": "processing",
            "start_time": datetime.utcnow().isoformat() + "Z",
            "details": {}
        }
        
        try:
            # Initialize formatted_articles before if/else to avoid scope issues
            formatted_articles = []
            sentiment_scores = []
            
            # Handle case where no articles were provided
            if not articles:
                step2_duration = (time.time() - step2_start) * 1000
                step2_data.update({
                    "status": "completed",
                    "duration_ms": round(step2_duration, 2),
                    "details": {
                        "articles_processed": 0,
                        "cache_hits": 0,
                        "cache_misses": 0,
                        "cache_hit_rate": 0,
                        "cache_stats": {},
                        "sentiment_scores": [],
                        "processed_at": datetime.utcnow().isoformat() + "Z",
                        "message": "No articles to process (all filtered out by relevance threshold)"
                    }
                })
                response["steps"].append(step2_data)
                # Continue to Step 3 with empty sentiment scores
            else:
                # Ensure articles are in correct format for LLM agent
                # LLM agent expects list of dicts with: id, title, source, published_at, url, summary, content
                for article in articles:
                    if isinstance(article, dict):
                        # Ensure all required fields exist
                        formatted_article = {
                            "id": article.get("id", ""),
                            "title": article.get("title", ""),
                            "source": article.get("source", "Unknown"),
                            "published_at": article.get("published_at", datetime.utcnow().isoformat() + "Z"),
                            "url": article.get("url"),
                            "summary": article.get("summary", ""),
                            "content": article.get("content", article.get("summary", ""))
                        }
                        formatted_articles.append(formatted_article)
                    elif hasattr(article, 'dict'):
                        art_dict = article.dict()
                        formatted_article = {
                            "id": art_dict.get("id", ""),
                            "title": art_dict.get("title", ""),
                            "source": art_dict.get("source", "Unknown"),
                            "published_at": art_dict.get("published_at", datetime.utcnow().isoformat() + "Z"),
                            "url": art_dict.get("url"),
                            "summary": art_dict.get("summary", ""),
                            "content": art_dict.get("content", art_dict.get("summary", ""))
                        }
                        formatted_articles.append(formatted_article)
                    else:
                        art_dict = dict(article)
                        formatted_article = {
                            "id": art_dict.get("id", ""),
                            "title": art_dict.get("title", ""),
                            "source": art_dict.get("source", "Unknown"),
                            "published_at": art_dict.get("published_at", datetime.utcnow().isoformat() + "Z"),
                            "url": art_dict.get("url"),
                            "summary": art_dict.get("summary", ""),
                            "content": art_dict.get("content", art_dict.get("summary", ""))
                        }
                        formatted_articles.append(formatted_article)
                
                # Process sentiment analysis only if we have articles
                sentiment_params = {
                    "articles": formatted_articles,
                    "use_cache": True,
                    "time_horizon": time_horizon  # Pass time horizon
                }
                sentiment_result = llm_agent.process(symbol, sentiment_params)
                
                step2_duration = (time.time() - step2_start) * 1000
                
                sentiment_scores = sentiment_result.get("sentiment_scores", [])
                cache_stats = sentiment_result.get("cache_stats", {})
                
                # Count cache hits/misses
                cache_hits = sum(1 for s in sentiment_scores if s.get("cached", False))
                cache_misses = len(sentiment_scores) - cache_hits
                
                step2_data.update({
                    "status": "completed" if sentiment_result.get("status") == "success" else "error",
                    "duration_ms": round(step2_duration, 2),
                    "details": {
                        "articles_processed": len(sentiment_scores),
                        "cache_hits": cache_hits,
                        "cache_misses": cache_misses,
                        "cache_hit_rate": round(cache_hits / len(sentiment_scores), 2) if sentiment_scores else 0,
                        "cache_stats": cache_stats,
                        "sentiment_scores": sentiment_scores,
                        "processed_at": sentiment_result.get("processed_at"),
                        "time_horizon": time_horizon
                    }
                })
                response["steps"].append(step2_data)
            
        except Exception as e:
            error_trace = traceback.format_exc()
            step2_data.update({
                "status": "error",
                "duration_ms": round((time.time() - step2_start) * 1000, 2),
                "error": str(e),
                "error_trace": error_trace,
                "details": {
                    "articles_received": len(articles) if 'articles' in locals() else 0,
                    "formatted_articles_count": len(formatted_articles) if 'formatted_articles' in locals() else 0,
                    "error_message": str(e),
                    "error_trace": error_trace
                }
            })
            response["steps"].append(step2_data)
            response["status"] = "error"
            response["error"] = f"LLM Sentiment Agent failed: {str(e)}"
            response["error_trace"] = error_trace
            response["total_duration_ms"] = round((time.time() - start_time) * 1000, 2)
            return response
        
        # Ensure step2_data is appended (should already be done, but safety check)
        if len(response["steps"]) < 2:
            response["steps"].append(step2_data)
        
        # ============================================
        # STEP 3: Sentiment Aggregator
        # ============================================
        step3_start = time.time()
        step3_data = {
            "agent": "sentiment_aggregator",
            "status": "processing",
            "start_time": datetime.utcnow().isoformat() + "Z",
            "details": {}
        }
        
        try:
            # Handle case where no sentiment scores (no articles processed)
            if not sentiment_scores:
                step3_duration = (time.time() - step3_start) * 1000
                step3_data.update({
                    "status": "completed",
                    "duration_ms": round(step3_duration, 2),
                    "details": {
                        "aggregated_sentiment": 0.0,
                        "sentiment_label": "neutral",
                        "confidence": 0.0,
                        "impact": "Low",
                        "news_count": 0,
                        "time_weighted": False,
                        "aggregated_at": datetime.utcnow().isoformat() + "Z",
                        "message": "No sentiment scores to aggregate (no articles passed relevance filter)"
                    }
                })
                response["steps"].append(step3_data)
                response["final_result"] = {
                    "symbol": symbol,
                    "aggregated_sentiment": 0.0,
                    "sentiment_label": "neutral",
                    "confidence": 0.0,
                    "impact": "Low",
                    "news_count": 0,
                    "time_weighted": False,
                    "message": "No articles found after relevance filtering"
                }
                response["total_duration_ms"] = round((time.time() - start_time) * 1000, 2)
                return response
            
            # Ensure sentiment_scores are in correct format (list of dicts)
            formatted_sentiment_scores = []
            for score in sentiment_scores:
                if isinstance(score, dict):
                    formatted_sentiment_scores.append(score)
                elif hasattr(score, 'dict'):
                    formatted_sentiment_scores.append(score.dict())
                else:
                    formatted_sentiment_scores.append(dict(score))
            
            # Process aggregation
            aggregation_params = {
                "sentiment_scores": formatted_sentiment_scores,
                "time_weighted": True,
                "calculate_impact": True
            }
            aggregation_result = aggregator_agent.process(symbol, aggregation_params)
            
            step3_duration = (time.time() - step3_start) * 1000
            
            step3_data.update({
                "status": "completed" if aggregation_result.get("status") == "success" else "error",
                "duration_ms": round(step3_duration, 2),
                "details": {
                    "aggregated_sentiment": aggregation_result.get("aggregated_sentiment", 0.0),
                    "sentiment_label": aggregation_result.get("sentiment_label", "neutral"),
                    "confidence": aggregation_result.get("confidence", 0.0),
                    "impact": aggregation_result.get("impact", "Low"),
                    "news_count": aggregation_result.get("news_count", 0),
                    "time_weighted": aggregation_result.get("time_weighted", False),
                    "aggregated_at": aggregation_result.get("aggregated_at")
                }
            })
            
            # Set final result
            response["final_result"] = {
                "symbol": symbol,
                "aggregated_sentiment": aggregation_result.get("aggregated_sentiment", 0.0),
                "sentiment_label": aggregation_result.get("sentiment_label", "neutral"),
                "confidence": aggregation_result.get("confidence", 0.0),
                "impact": aggregation_result.get("impact", "Low"),
                "news_count": aggregation_result.get("news_count", 0),
                "time_weighted": aggregation_result.get("time_weighted", False)
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            step3_data.update({
                "status": "error",
                "duration_ms": round((time.time() - step3_start) * 1000, 2),
                "error": str(e),
                "error_trace": error_trace
            })
            response["steps"].append(step3_data)
            response["status"] = "error"
            response["error"] = f"Sentiment Aggregator failed: {str(e)}"
            response["error_trace"] = error_trace
            response["total_duration_ms"] = round((time.time() - start_time) * 1000, 2)
            return response
        
        response["steps"].append(step3_data)
        
        # Calculate total duration
        response["total_duration_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return response
        
    except Exception as e:
        return {
            "input": {
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "steps": [],
            "final_result": None,
            "total_duration_ms": round((time.time() - start_time) * 1000, 2),
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """Health check for the visualizer endpoint."""
    try:
        news_agent, llm_agent, aggregator_agent = _get_agents()
        return {
            "status": "healthy",
            "agents_initialized": {
                "news_fetch_agent": news_agent.initialized if news_agent else False,
                "llm_sentiment_agent": llm_agent.initialized if llm_agent else False,
                "sentiment_aggregator": aggregator_agent.initialized if aggregator_agent else False
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

