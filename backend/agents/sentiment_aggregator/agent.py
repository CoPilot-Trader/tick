"""
Sentiment Aggregator - Main agent implementation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.interfaces.base_agent import BaseAgent

# Import aggregation components
from .aggregation import TimeWeightedAggregator, ImpactScorer
from .interfaces import AggregatedSentiment

logger = logging.getLogger(__name__)


class SentimentAggregator(BaseAgent):
    """
    Sentiment Aggregator for combining multiple sentiment outputs.
    
    This agent:
    1. Receives sentiment scores from LLM Sentiment Agent
    2. Applies time-weighted aggregation (recent news weighted more)
    3. Calculates impact score (High/Medium/Low)
    4. Returns aggregated sentiment to Fusion Agent
    
    Developer: Developer 1
    Milestone: M3 - Sentiment & Fusion
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Sentiment Aggregator."""
        super().__init__(name="sentiment_aggregator", config=config)
        self.version = "1.0.0"
        
        # Configuration
        self.use_time_weighting = self.config.get("use_time_weighting", True)
        self.enable_impact_scoring = self.config.get("calculate_impact", True)
        
        # Initialize components (will be set in initialize())
        self.time_aggregator: Optional[TimeWeightedAggregator] = None
        self.impact_scorer: Optional[ImpactScorer] = None
    
    def initialize(self) -> bool:
        """
        Initialize the Sentiment Aggregator.
        
        Sets up:
        - Time-weighted aggregator
        - Impact scorer
        """
        try:
            # Initialize time-weighted aggregator
            if self.use_time_weighting:
                self.time_aggregator = TimeWeightedAggregator(config={
                    "decay_type": self.config.get("decay_type", "exponential"),
                    "half_life_hours": self.config.get("half_life_hours", 24),
                    "max_age_hours": self.config.get("max_age_hours", 168)
                })
            else:
                self.time_aggregator = TimeWeightedAggregator()
            
            # Initialize impact scorer
            if self.enable_impact_scoring:
                self.impact_scorer = ImpactScorer(config={
                    "high_impact_threshold": self.config.get("high_impact_threshold", 0.7),
                    "medium_impact_threshold": self.config.get("medium_impact_threshold", 0.4),
                    "min_news_count_high": self.config.get("min_news_count_high", 10),
                    "min_news_count_medium": self.config.get("min_news_count_medium", 5)
                })
            else:
                self.impact_scorer = ImpactScorer()
            
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing Sentiment Aggregator: {e}", exc_info=True)
            self.initialized = False
            return False
    
    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Aggregate sentiment for a given symbol.
        
        This is the main entry point that:
        1. Receives sentiment scores from LLM Sentiment Agent
        2. Applies time-weighted aggregation
        3. Calculates impact score
        4. Returns aggregated sentiment
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            params: Optional parameters:
                   - sentiment_scores: List of sentiment scores (required)
                   - time_weighted: Use time weighting (default: True)
                   - calculate_impact: Calculate impact score (default: True)
                   - time_horizon: Prediction time horizon (adjusts time weighting)
            
        Returns:
            Dictionary with aggregated sentiment:
            {
                "symbol": str,
                "aggregated_sentiment": float,
                "sentiment_label": str,
                "confidence": float,
                "impact": str,
                "news_count": int,
                "time_weighted": bool,
                "time_horizon": str,
                "aggregated_at": str,
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
        sentiment_scores = params.get("sentiment_scores", [])
        time_weighted = params.get("time_weighted", self.use_time_weighting)
        time_horizon = params.get("time_horizon", "1d")  # Default to 1 day
        
        # Get horizon-specific confidence threshold
        min_confidence, min_articles = self._get_horizon_thresholds(time_horizon)
        
        # Filter sentiment scores by confidence threshold
        if min_confidence > 0:
            original_count = len(sentiment_scores)
            sentiment_scores = [
                score for score in sentiment_scores
                if score.get("confidence", 0.5) >= min_confidence
            ]
            filtered_count = original_count - len(sentiment_scores)
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} low-confidence articles (threshold: {min_confidence:.2f})")
        
        # Check minimum articles requirement
        if len(sentiment_scores) < min_articles:
            logger.warning(f"Only {len(sentiment_scores)} articles (minimum: {min_articles} for {time_horizon})")
        
        if not sentiment_scores:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "No sentiment scores provided",
                "aggregated_sentiment": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "impact": "Low",
                "news_count": 0,
                "time_weighted": False,
                "aggregated_at": datetime.utcnow().isoformat() + "Z"
            }
        
        try:
            # Step 1: Update time aggregator with time_horizon if provided
            if time_weighted and self.time_aggregator and time_horizon:
                # Adjust aggregator for this horizon
                self.time_aggregator._adjust_for_horizon(time_horizon)
            
            # Step 2: Aggregate sentiment scores
            if time_weighted and self.time_aggregator:
                aggregated = self.time_aggregator.aggregate(sentiment_scores, symbol)
            else:
                # Simple aggregation without time weighting
                if self.time_aggregator:
                    aggregated = self.time_aggregator.aggregate_simple(sentiment_scores, symbol)
                else:
                    # Fallback: simple average
                    sentiments = [s.get("sentiment_score", 0.0) for s in sentiment_scores]
                    confidences = [s.get("confidence", 0.7) for s in sentiment_scores]
                    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.7
                    
                    aggregated = {
                        "aggregated_sentiment": avg_sentiment,
                        "sentiment_label": "positive" if avg_sentiment > 0.3 else ("negative" if avg_sentiment < -0.3 else "neutral"),
                        "confidence": avg_confidence,
                        "news_count": len(sentiment_scores),
                        "time_weighted": False
                    }
            
            # Step 2: Calculate impact score
            impact = "Low"
            if self.enable_impact_scoring and self.impact_scorer:
                # Get recency from weights if available
                weights = aggregated.get("weights_applied", [])
                recency = None
                if weights:
                    recency = self.impact_scorer.calculate_recency_score(weights)
                
                impact = self.impact_scorer.calculate_impact(
                    aggregated_sentiment=aggregated["aggregated_sentiment"],
                    news_count=aggregated["news_count"],
                    recency=recency,
                    confidence=aggregated.get("confidence")
                )
            else:
                # Simple impact calculation
                if self.impact_scorer:
                    impact = self.impact_scorer.calculate_impact_simple(
                        aggregated["aggregated_sentiment"],
                        aggregated["news_count"]
                    )
            
            # Step 3: Return aggregated result
            return {
                "symbol": symbol,
                "aggregated_sentiment": aggregated["aggregated_sentiment"],
                "sentiment_label": aggregated["sentiment_label"],
                "confidence": aggregated["confidence"],
                "impact": impact,
                "news_count": aggregated["news_count"],
                "time_weighted": aggregated.get("time_weighted", False),
                "time_horizon": time_horizon,
                "aggregated_at": datetime.utcnow().isoformat() + "Z",
                "status": "success"
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "status": "error",
                "message": f"Error aggregating sentiment: {str(e)}",
                "aggregated_sentiment": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "impact": "Low",
                "news_count": 0,
                "time_weighted": False,
                "aggregated_at": datetime.utcnow().isoformat() + "Z"
            }
    
    def aggregate(self, sentiment_scores: List[Dict[str, Any]], symbol: str, time_weighted: bool = True) -> Dict[str, Any]:
        """
        Aggregate multiple sentiment scores (convenience method).
        
        Args:
            sentiment_scores: List of sentiment scores from LLM Sentiment Agent
            symbol: Stock symbol
            time_weighted: Use time-weighted aggregation
        
        Returns:
            Dictionary with aggregated sentiment
        
        Example:
            aggregated = aggregator.aggregate(sentiment_scores, "AAPL")
        """
        return self.process(symbol, params={
            "sentiment_scores": sentiment_scores,
            "time_weighted": time_weighted
        })
    
    def calculate_impact(
        self,
        aggregated_sentiment: float,
        news_count: int,
        recency: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> str:
        """
        Calculate impact score (High/Medium/Low) (utility method).
        
        Args:
            aggregated_sentiment: Aggregated sentiment score
            news_count: Number of news articles
            recency: Recency score (optional)
            confidence: Confidence score (optional)
        
        Returns:
            Impact level: "High", "Medium", or "Low"
        
        Example:
            impact = aggregator.calculate_impact(0.75, 15, recency=0.9)
            # Returns: "High"
        """
        if self.impact_scorer:
            return self.impact_scorer.calculate_impact(
                aggregated_sentiment, news_count, recency, confidence
            )
        return "Low"
    
    def _get_horizon_thresholds(self, time_horizon: str) -> tuple:
        """
        Get confidence threshold and minimum articles based on time horizon.
        
        Short-term predictions require higher confidence and fewer articles.
        Long-term predictions can be more lenient with more articles.
        
        Args:
            time_horizon: Prediction time horizon ("1s", "1m", "1h", "1d", "1w", "1mo", "1y")
        
        Returns:
            Tuple of (min_confidence, min_articles)
        """
        time_horizon = time_horizon.lower().strip()
        
        # Horizon-specific thresholds
        thresholds = {
            "1s": (0.8, 3),   # Very strict for 1-second predictions
            "1m": (0.75, 5),  # Strict for 1-minute predictions
            "1h": (0.7, 8),   # Moderate for hourly predictions
            "1d": (0.65, 10), # Moderate for daily predictions
            "1w": (0.6, 15),  # Lenient for weekly predictions
            "1mo": (0.55, 20), # More lenient for monthly predictions
            "1y": (0.5, 25)   # Most lenient for yearly predictions
        }
        
        return thresholds.get(time_horizon, (0.65, 10))  # Default to daily thresholds
    
    def health_check(self) -> Dict[str, Any]:
        """Check Sentiment Aggregator health."""
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "time_weighting_enabled": self.use_time_weighting,
            "impact_scoring_enabled": self.enable_impact_scoring
        }
