"""
LLM Sentiment Agent - Main agent implementation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.interfaces.base_agent import BaseAgent

# Import components
from .llm import MockGPT4Client, GPT4Client, PromptTemplates
from .cache import CacheManager
from .optimization import CostOptimizer
from .interfaces import SentimentScore

logger = logging.getLogger(__name__)


class LLMSentimentAgent(BaseAgent):
    """
    LLM Sentiment Agent for processing news with GPT-4.
    
    This agent:
    1. Receives news articles from News Fetch Agent
    2. Checks semantic cache for similar articles
    3. If cache miss, analyzes with GPT-4 (or mock for testing)
    4. Stores results in cache
    5. Returns sentiment scores to Sentiment Aggregator
    
    Developer: Developer 1
    Milestone: M3 - Sentiment & Fusion
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM Sentiment Agent."""
        super().__init__(name="llm_sentiment_agent", config=config)
        self.version = "1.0.0"
        self.model = "gpt-4"
        self.cache_hit_rate_target = 0.60
        
        # Configuration
        self.use_mock_data = self.config.get("use_mock_data", True)  # Default to mock for testing
        self.use_cache = self.config.get("use_cache", True)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)
        
        # Initialize components (will be set in initialize())
        self.llm_client = None
        self.cache_manager: Optional[CacheManager] = None
        self.cost_optimizer: Optional[CostOptimizer] = None
        self.prompt_templates = PromptTemplates()
    
    def initialize(self) -> bool:
        """
        Initialize the LLM Sentiment Agent.
        
        Sets up:
        - LLM client (Mock for testing, or GPT-4 for production)
        - Semantic cache manager
        - Cost optimizer
        """
        try:
            # Initialize LLM client
            if self.use_mock_data:
                # Use mock client for testing
                self.llm_client = MockGPT4Client()
            else:
                # Use real GPT-4 client (requires API key)
                api_key = self.config.get("openai_api_key")
                if not api_key:
                    raise ValueError("OpenAI API key is required when use_mock_data=False")
                self.llm_client = GPT4Client(config={"api_key": api_key})
            
            # Initialize cache manager
            if self.use_cache:
                self.cache_manager = CacheManager(config={
                    "similarity_threshold": self.similarity_threshold,
                    "enable_cache": True
                })
            else:
                self.cache_manager = CacheManager(config={"enable_cache": False})
            
            # Initialize cost optimizer
            self.cost_optimizer = CostOptimizer()
            
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing LLM Sentiment Agent: {e}", exc_info=True)
            self.initialized = False
            return False
    
    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process sentiment analysis for news articles.
        
        This is the main entry point that:
        1. Receives articles from News Fetch Agent
        2. Analyzes sentiment for each article (with caching)
        3. Returns sentiment scores
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            params: Optional parameters:
                   - articles: List of news articles (required)
                   - use_cache: Use semantic cache (default: True)
                   - batch_size: Batch size for processing (default: 5)
                   - time_horizon: Prediction time horizon (passed through for context)
            
        Returns:
            Dictionary with sentiment scores:
            {
                "symbol": str,
                "sentiment_scores": List[Dict],
                "processed_at": str,
                "cache_stats": Dict,
                "time_horizon": str,
                "status": str
            }
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized. Call initialize() first."
            }
        
        params = params or {}
        articles = params.get("articles", [])
        use_cache = params.get("use_cache", self.use_cache)
        time_horizon = params.get("time_horizon", "1d")  # Pass through time horizon
        
        if not articles:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "No articles provided",
                "sentiment_scores": [],
                "processed_at": datetime.utcnow().isoformat() + "Z"
            }
        
        try:
            # Analyze sentiment for all articles
            sentiment_scores = []
            
            # Get confidence threshold based on time horizon (if provided)
            time_horizon = params.get("time_horizon", "1d")
            min_confidence = self._get_confidence_threshold(time_horizon)
            
            for article in articles:
                # Analyze sentiment (with caching)
                result = self.analyze_sentiment(article, symbol, use_cache=use_cache)
                
                # Filter by confidence threshold (only include high-confidence articles)
                if result.get("confidence", 0.5) >= min_confidence:
                    sentiment_scores.append(result)
                # else: Skip low-confidence articles
            
            # Get cache statistics
            cache_stats = {}
            if self.cache_manager:
                cache_stats = self.cache_manager.get_stats()
            
            # Return results with confidence filtering info
            filtered_count = len(articles) - len(sentiment_scores)
            return {
                "symbol": symbol,
                "sentiment_scores": sentiment_scores,
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "cache_stats": cache_stats,
                "status": "success",
                "total_articles": len(articles),
                "total_analyzed": len(sentiment_scores),
                "filtered_by_confidence": filtered_count,
                "confidence_threshold": min_confidence,
                "time_horizon": time_horizon
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "status": "error",
                "message": f"Error processing sentiment: {str(e)}",
                "sentiment_scores": [],
                "processed_at": datetime.utcnow().isoformat() + "Z"
            }
    
    def analyze_sentiment(self, article: Dict[str, Any], symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze sentiment for a news article.
        
        Pipeline:
        1. Check semantic cache (if enabled)
        2. If cache hit, return cached result
        3. If cache miss, analyze with GPT-4
        4. Store result in cache
        5. Return sentiment score
        
        Args:
            article: News article from News Fetch Agent
            symbol: Stock symbol
            use_cache: Use semantic cache
        
        Returns:
            Dictionary with sentiment score:
            {
                "article_id": str,
                "sentiment_score": float (-1.0 to +1.0),
                "sentiment_label": str (positive/neutral/negative),
                "confidence": float (0.0 to 1.0),
                "reasoning": str,
                "cached": bool,
                "processed_at": str
            }
        
        Example:
            result = agent.analyze_sentiment(article, "AAPL")
            # Returns: {"article_id": "article_123", "sentiment_score": 0.75, ...}
        """
        article_id = article.get("id", f"article_{hash(article.get('title', ''))}")
        
        # Step 1: Check cache
        if use_cache and self.cache_manager:
            cached_result = self.cache_manager.get_cached_sentiment(article, symbol)
            if cached_result:
                # Cache hit - return cached result
                return {
                    "article_id": article_id,
                    "symbol": symbol,
                    "sentiment_score": cached_result.get("sentiment_score", 0.0),
                    "sentiment_label": cached_result.get("sentiment_label", "neutral"),
                    "confidence": cached_result.get("confidence", 0.7),
                    "reasoning": cached_result.get("reasoning", "Cached from similar article"),
                    "cached": True,
                    "processed_at": datetime.utcnow().isoformat() + "Z"
                }
        
        # Step 2: Cache miss - analyze with GPT-4
        # Generate prompt
        company_name = self._get_company_name(symbol)
        prompt = self.prompt_templates.get_sentiment_prompt(article, symbol, company_name)
        
        # Analyze with LLM client
        llm_result = self.llm_client.analyze_sentiment(article, symbol)
        
        # Step 3: Store in cache
        if use_cache and self.cache_manager:
            self.cache_manager.store_sentiment(article, llm_result, symbol)
        
        # Step 4: Return result
        return {
            "article_id": article_id,
            "symbol": symbol,
            "sentiment_score": llm_result.get("sentiment_score", 0.0),
            "sentiment_label": llm_result.get("sentiment_label", "neutral"),
            "confidence": llm_result.get("confidence", 0.7),
            "reasoning": llm_result.get("reasoning", ""),
            "cached": False,
            "processed_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def batch_analyze(self, articles: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
        """
        Batch analyze sentiment for multiple articles.
        
        Args:
            articles: List of news articles
            symbol: Stock symbol
        
        Returns:
            List of sentiment scores
        
        Example:
            results = agent.batch_analyze(articles, "AAPL")
        """
        results = []
        for article in articles:
            result = self.analyze_sentiment(article, symbol)
            results.append(result)
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get semantic cache statistics.
        
        Returns:
            Dictionary with cache stats:
            {
                "hits": int,
                "misses": int,
                "total_requests": int,
                "hit_rate": float,
                "cache_info": dict
            }
        
        Example:
            stats = agent.get_cache_stats()
            print(f"Cache hit rate: {stats['hit_rate']:.2%}")
        """
        if self.cache_manager:
            return self.cache_manager.get_stats()
        return {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "hit_rate": 0.0,
            "cache_info": {"enabled": False}
        }
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """
        Get cost statistics.
        
        Returns:
            Dictionary with cost stats
        """
        if self.cost_optimizer:
            return self.cost_optimizer.get_cost_stats()
        return {}
    
    def _get_confidence_threshold(self, time_horizon: str) -> float:
        """
        Get confidence threshold based on time horizon.
        
        Short-term predictions require higher confidence, long-term can be more lenient.
        
        Args:
            time_horizon: Prediction time horizon ("1s", "1m", "1h", "1d", "1w", "1mo", "1y")
        
        Returns:
            Minimum confidence threshold (0.0 to 1.0)
        """
        time_horizon = time_horizon.lower().strip()
        
        # Horizon-specific confidence thresholds
        thresholds = {
            "1s": 0.8,   # Very strict for 1-second predictions
            "1m": 0.75,  # Strict for 1-minute predictions
            "1h": 0.7,   # Moderate for hourly predictions
            "1d": 0.65,  # Moderate for daily predictions
            "1w": 0.6,   # Lenient for weekly predictions
            "1mo": 0.55, # More lenient for monthly predictions
            "1y": 0.5    # Most lenient for yearly predictions
        }
        
        return thresholds.get(time_horizon, 0.65)  # Default to 0.65 for daily
    
    def _get_company_name(self, symbol: str) -> str:
        """
        Get company name for a symbol (helper method).
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Company name
        """
        # Simple mapping (can be extended)
        company_names = {
            "AAPL": "Apple Inc",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc",
            "XOM": "Exxon Mobil Corporation",
            "CVX": "Chevron Corporation",
            "JNJ": "Johnson & Johnson",
            "PFE": "Pfizer Inc",
            "JPM": "JPMorgan Chase",
            "BAC": "Bank of America",
            "GS": "Goldman Sachs"
        }
        return company_names.get(symbol.upper(), symbol)
    
    def health_check(self) -> Dict[str, Any]:
        """Check LLM Sentiment Agent health."""
        cache_stats = self.get_cache_stats()
        hit_rate = cache_stats.get("hit_rate", 0.0)
        
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "model": self.model,
            "cache_hit_rate_target": self.cache_hit_rate_target,
            "current_cache_hit_rate": hit_rate,
            "cache_enabled": self.use_cache,
            "using_mock_data": self.use_mock_data
        }
