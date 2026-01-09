"""
News Fetch Agent - Main agent implementation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from core.interfaces.base_agent import BaseAgent

# Import collectors, filters, and utils
from .collectors import (
    MockNewsCollector, 
    BaseNewsCollector,
    FinnhubCollector,
    NewsAPICollector,
    AlphaVantageCollector
)
from .filters import RelevanceFilter, DuplicateFilter
from .utils import SectorMapper, DateRangeCalculator, get_logger
from .interfaces import NewsResponse, NewsArticle

logger = get_logger(__name__)


class NewsFetchAgent(BaseAgent):
    """
    News Fetch Agent for collecting financial news.
    
    Developer: Developer 1
    Milestone: M3 - Sentiment & Fusion
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize News Fetch Agent."""
        super().__init__(name="news_fetch_agent", config=config)
        self.version = "1.0.0"
        self.sources = ["finnhub", "newsapi", "alpha_vantage"]
        
        # Initialize components
        self.collectors: List[BaseNewsCollector] = []
        self.relevance_filter: Optional[RelevanceFilter] = None
        self.duplicate_filter: Optional[DuplicateFilter] = None
        self.sector_mapper: Optional[SectorMapper] = None
        
        # Configuration
        self.use_mock_data = self.config.get("use_mock_data", True)  # Default to mock for testing
        self.min_relevance_score = self.config.get("min_relevance_score", 0.5)
        self.max_articles = self.config.get("max_articles", 50)
    
    def initialize(self) -> bool:
        """
        Initialize the News Fetch Agent.
        
        Sets up:
        - News collectors (Mock for testing, or real APIs for production)
        - Relevance filter
        - Duplicate filter
        - Sector mapper
        """
        try:
            # Initialize collectors
            if self.use_mock_data:
                # Use mock collector for testing
                mock_collector = MockNewsCollector()
                self.collectors.append(mock_collector)
            else:
                # Initialize real API collectors if API keys are provided
                finnhub_key = self.config.get("finnhub_api_key")
                newsapi_key = self.config.get("newsapi_key")
                alphavantage_key = self.config.get("alpha_vantage_api_key")
                
                # Check if keys are non-empty strings
                has_finnhub = finnhub_key and isinstance(finnhub_key, str) and finnhub_key.strip()
                has_newsapi = newsapi_key and isinstance(newsapi_key, str) and newsapi_key.strip()
                has_alphavantage = alphavantage_key and isinstance(alphavantage_key, str) and alphavantage_key.strip()
                
                # Add collectors for which we have valid API keys
                if has_finnhub:
                    try:
                        finnhub_collector = FinnhubCollector(config={"api_key": finnhub_key.strip()})
                        self.collectors.append(finnhub_collector)
                        logger.info("Finnhub collector initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize Finnhub collector: {e}")
                
                if has_newsapi:
                    try:
                        newsapi_collector = NewsAPICollector(config={"api_key": newsapi_key.strip()})
                        self.collectors.append(newsapi_collector)
                        logger.info("NewsAPI collector initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize NewsAPI collector: {e}")
                
                if has_alphavantage:
                    try:
                        alphavantage_collector = AlphaVantageCollector(config={"api_key": alphavantage_key.strip()})
                        self.collectors.append(alphavantage_collector)
                        logger.info("Alpha Vantage collector initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize Alpha Vantage collector: {e}")
                
                # If no collectors were added, fall back to mock
                if not self.collectors:
                    logger.warning("No valid API keys provided. Falling back to mock collector.")
                    mock_collector = MockNewsCollector()
                    self.collectors.append(mock_collector)
            
            # Initialize filters
            self.relevance_filter = RelevanceFilter(config={
                "min_relevance_score": self.min_relevance_score
            })
            self.duplicate_filter = DuplicateFilter()
            
            # Initialize sector mapper
            self.sector_mapper = SectorMapper()
            
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing News Fetch Agent: {e}", exc_info=True)
            self.initialized = False
            return False
    
    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch and process news for a given symbol.
        
        This is the main entry point that:
        1. Fetches news from all collectors
        2. Scores articles by relevance
        3. Filters by relevance threshold
        4. Removes duplicates
        5. Returns processed articles
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            params: Optional parameters:
                   - limit: Maximum number of articles (default: from config)
                   - min_relevance: Minimum relevance score (default: from config)
                   - sources: List of sources to use (default: all)
                   - time_horizon: Prediction time horizon ("1s", "1m", "1h", "1d", "1w", "1mo", "1y") (default: "1d")
            
        Returns:
            Dictionary with processed news articles in NewsResponse format
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized. Call initialize() first."
            }
        
        params = params or {}
        limit = params.get("limit", self.max_articles)
        min_relevance = params.get("min_relevance", self.min_relevance_score)
        time_horizon = params.get("time_horizon", "1d")  # Default to 1 day
        
        try:
            # Calculate date range based on time horizon
            from_date, to_date = DateRangeCalculator.calculate(time_horizon, symbol)
            
            # Prepare collector params with date range (NO LIMIT - fetch all available)
            # We'll apply the limit after combining articles from all collectors
            collector_params = {
                "from_date": from_date,
                "to_date": to_date,
                "time_horizon": time_horizon
            }
            
            # Step 1: Fetch news from all collectors
            all_articles = []
            sources_used = []
            api_usage_info = []  # Track API usage for each collector
            
            for collector in self.collectors:
                try:
                    articles = collector.fetch_news(symbol, collector_params)
                    if articles:
                        all_articles.extend(articles)
                        sources_used.append(collector.get_source_name())
                    
                    # Get API usage info from collector
                    usage_info = collector.get_api_usage_info()
                    api_usage_info.append(usage_info)
                except Exception as e:
                    logger.warning(f"Error fetching from {collector.get_source_name()}: {e}")
                    # Still try to get usage info even if fetch failed
                    try:
                        usage_info = collector.get_api_usage_info()
                        api_usage_info.append(usage_info)
                    except:
                        pass
                    continue
            
            # Dynamic window adjustment: If not enough articles, expand window and retry
            min_articles_required = min(limit, 10)  # Require at least min(limit, 10) articles
            max_expansions = 2  # Maximum number of window expansions
            expansion_count = 0
            
            while len(all_articles) < min_articles_required and expansion_count < max_expansions:
                # Expand window by 50%
                from_date, to_date = DateRangeCalculator.expand_window(time_horizon, from_date, to_date, multiplier=1.5)
                expansion_count += 1
                
                # Update collector params with expanded date range
                collector_params["from_date"] = from_date
                collector_params["to_date"] = to_date
                
                # Fetch again with expanded window
                additional_articles = []
                for collector in self.collectors:
                    try:
                        articles = collector.fetch_news(symbol, collector_params)
                        if articles:
                            additional_articles.extend(articles)
                    except Exception as e:
                        logger.warning(f"Error fetching from {collector.get_source_name()}: {e}")
                        continue
                
                # Add new articles (avoid duplicates by checking IDs/URLs)
                existing_ids = {a.get("id") or a.get("url") for a in all_articles}
                for article in additional_articles:
                    article_id = article.get("id") or article.get("url")
                    if article_id not in existing_ids:
                        all_articles.append(article)
                        existing_ids.add(article_id)
                
                # If we have enough now, break
                if len(all_articles) >= min_articles_required:
                    break
            
            # Apply max_articles limit BEFORE filtering (so raw_articles_count respects the limit)
            # This ensures we don't fetch more articles than requested
            if len(all_articles) > limit:
                # Sort by a simple criteria (e.g., published date) before limiting
                # This ensures we get the most recent articles
                try:
                    all_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)
                except:
                    pass  # If sorting fails, just take first N
                all_articles = all_articles[:limit]
            
            # Track raw count AFTER applying max_articles limit
            raw_articles_count = len(all_articles)
            
            if not all_articles:
                # Determine data source
                is_mock = (api_usage_info and all(info.get("is_mock", False) for info in api_usage_info)) if api_usage_info else True
                return {
                    "symbol": symbol,
                    "articles": [],
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                    "total_count": 0,
                    "raw_articles_count": raw_articles_count,  # Include raw count even if 0
                    "sources": sources_used,
                    "api_usage": api_usage_info,  # Include API usage even if no articles
                    "data_source": "mock" if is_mock else ("api" if api_usage_info else "unknown"),
                    "status": "success",
                    "message": "No articles found"
                }
            
            # Step 2: Score articles by relevance
            if self.relevance_filter:
                scored_articles = self.relevance_filter.score_articles(all_articles, symbol)
            else:
                # If no filter, assign default score
                scored_articles = all_articles
                for article in scored_articles:
                    article["relevance_score"] = 0.5
            
            # Step 3: Filter by relevance threshold
            if self.relevance_filter:
                filtered_articles = self.relevance_filter.filter_by_threshold(
                    scored_articles, 
                    min_score=min_relevance
                )
            else:
                filtered_articles = scored_articles
            
            # Step 4: Remove duplicates
            if self.duplicate_filter:
                unique_articles = self.duplicate_filter.remove_duplicates(filtered_articles)
            else:
                unique_articles = filtered_articles
            
            # Step 5: Sort by relevance (highest first)
            if self.relevance_filter:
                sorted_articles = self.relevance_filter.sort_by_relevance(unique_articles, reverse=True)
            else:
                sorted_articles = unique_articles
            
            # Step 6: Apply limit (already applied earlier, but keep as safety)
            # Note: Articles are already limited to max_articles before filtering
            final_articles = sorted_articles[:limit]
            
            # Step 7: Convert to NewsArticle format (ensure relevance_score is present)
            news_articles = []
            for article in final_articles:
                # Ensure all required fields are present
                news_article = {
                    "id": article.get("id", ""),
                    "title": article.get("title", ""),
                    "source": article.get("source", "Unknown"),
                    "published_at": article.get("published_at", datetime.utcnow().isoformat() + "Z"),
                    "url": article.get("url"),
                    "summary": article.get("summary"),
                    "content": article.get("content"),
                    "relevance_score": article.get("relevance_score", 0.0)
                }
                news_articles.append(news_article)
            
            # Return in NewsResponse format
            return {
                "symbol": symbol,
                "articles": news_articles,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "total_count": len(news_articles),
                "raw_articles_count": raw_articles_count,  # Raw count before filtering
                "sources": sources_used,
                "time_horizon": time_horizon,
                "date_range": {
                    "from": from_date.isoformat(),
                    "to": to_date.isoformat()
                },
                "api_usage": api_usage_info,  # Add API usage information
                "data_source": "mock" if (api_usage_info and all(info.get("is_mock", False) for info in api_usage_info)) else ("api" if api_usage_info else "unknown"),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "status": "error",
                "message": f"Error processing news: {str(e)}",
                "articles": [],
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "total_count": 0,
                "sources": []
            }
    
    def fetch_news(self, symbol: str, sources: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Fetch news from specified sources (convenience method).
        
        Args:
            symbol: Stock symbol
            sources: List of sources (default: all)
            limit: Maximum number of articles
            
        Returns:
            Dictionary with news articles (same as process method)
        """
        return self.process(symbol, params={"limit": limit})
    
    def filter_relevance(self, articles: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
        """
        Filter and score news articles by relevance (utility method).
        
        Args:
            articles: List of news articles
            symbol: Stock symbol
            
        Returns:
            Filtered and scored articles
        """
        if not self.relevance_filter:
            return articles
        
        scored = self.relevance_filter.score_articles(articles, symbol)
        filtered = self.relevance_filter.filter_by_threshold(scored)
        return self.relevance_filter.sort_by_relevance(filtered)
    
    def health_check(self) -> Dict[str, Any]:
        """Check News Fetch Agent health."""
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "sources": self.sources
        }

