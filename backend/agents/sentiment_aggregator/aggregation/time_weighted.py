"""
Time-Weighted Aggregation

This module provides time-weighted sentiment aggregation.
Recent news articles are weighted more heavily than older ones.

Why Time-Weighted?
- Recent news is more relevant for current sentiment
- Market sentiment changes quickly
- Older news may be outdated
- Balances recency with overall sentiment
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math


class TimeWeightedAggregator:
    """
    Time-weighted sentiment aggregator.
    
    Weights recent news articles more heavily than older ones.
    Uses exponential decay or linear decay for time weighting.
    
    Example:
        aggregator = TimeWeightedAggregator()
        aggregated = aggregator.aggregate(sentiment_scores, symbol="AAPL")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize time-weighted aggregator.
        
        Args:
            config: Optional configuration:
                   - decay_type: "exponential" or "linear" (default: "exponential")
                   - half_life_hours: Hours for weight to decay to 50% (default: 24)
                   - max_age_hours: Maximum age in hours (default: 168 = 7 days)
                   - time_horizon: Prediction time horizon (adjusts weighting automatically)
        """
        self.config = config or {}
        self.decay_type = self.config.get("decay_type", "exponential")
        self.half_life_hours = self.config.get("half_life_hours", 24)
        self.max_age_hours = self.config.get("max_age_hours", 168)  # 7 days
        
        # Adjust parameters based on time_horizon if provided
        time_horizon = self.config.get("time_horizon", "1d")
        self._adjust_for_horizon(time_horizon)
    
    def _calculate_time_weight(self, article_time: datetime, current_time: datetime) -> float:
        """
        Calculate time weight for an article.
        
        Args:
            article_time: When the article was published
            current_time: Current time (for reference)
        
        Returns:
            Weight between 0.0 and 1.0
            1.0 = Very recent (within last hour)
            0.0 = Very old (beyond max_age)
        
        Example:
            weight = aggregator._calculate_time_weight(article_time, now)
            # Returns: 0.95 for recent article, 0.3 for old article
        """
        # Calculate age in hours
        age_hours = (current_time - article_time).total_seconds() / 3600
        
        # If beyond max age, return 0
        if age_hours > self.max_age_hours:
            return 0.0
        
        if self.decay_type == "exponential":
            # Exponential decay: weight = 0.5^(age / half_life)
            weight = math.pow(0.5, age_hours / self.half_life_hours)
        else:
            # Linear decay: weight = 1 - (age / max_age)
            weight = 1.0 - (age_hours / self.max_age_hours)
        
        # Ensure weight is between 0 and 1
        return max(0.0, min(1.0, weight))
    
    def _adjust_for_horizon(self, time_horizon: str) -> None:
        """
        Adjust time weighting parameters based on prediction time horizon.
        
        Different horizons require different decay rates:
        - Short horizons (1s, 1m): Very fast decay (minutes)
        - Medium horizons (1h, 1d): Moderate decay (hours/days)
        - Long horizons (1w, 1mo, 1y): Slow decay (days/weeks)
        
        Args:
            time_horizon: Prediction time horizon ("1s", "1m", "1h", "1d", "1w", "1mo", "1y")
        """
        time_horizon = time_horizon.lower().strip()
        
        if time_horizon in ["1s", "1m"]:
            # Very short horizons: decay in minutes
            self.half_life_hours = 0.1  # 6 minutes
            self.max_age_hours = 0.5    # 30 minutes
        elif time_horizon == "1h":
            # Hourly horizon: decay in hours
            self.half_life_hours = 2    # 2 hours
            self.max_age_hours = 6      # 6 hours
        elif time_horizon == "1d":
            # Daily horizon: decay in days
            self.half_life_hours = 24   # 1 day
            self.max_age_hours = 72     # 3 days
        elif time_horizon == "1w":
            # Weekly horizon: decay over week
            self.half_life_hours = 72   # 3 days
            self.max_age_hours = 168    # 7 days
        elif time_horizon == "1mo":
            # Monthly horizon: decay over month
            self.half_life_hours = 168  # 7 days
            self.max_age_hours = 720    # 30 days
        elif time_horizon == "1y":
            # Yearly horizon: slow decay
            self.half_life_hours = 720  # 30 days
            self.max_age_hours = 8760   # 365 days
        # else: use defaults (already set)
    
    def _parse_datetime(self, time_str: str) -> datetime:
        """
        Parse datetime string to datetime object.
        
        Args:
            time_str: ISO format datetime string
        
        Returns:
            Datetime object (timezone-aware)
        """
        try:
            # Try ISO format with Z
            if time_str.endswith('Z'):
                time_str = time_str[:-1] + '+00:00'
            elif '+' not in time_str and time_str.count(':') >= 2:
                # Add UTC timezone if not present
                time_str = time_str + '+00:00'
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            # Ensure timezone-aware
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            # Fallback to current time (timezone-aware)
            from datetime import timezone
            return datetime.now(timezone.utc)
    
    def aggregate(self, sentiment_scores: List[Dict[str, Any]], symbol: str, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Aggregate sentiment scores with time weighting.
        
        Args:
            sentiment_scores: List of sentiment scores from LLM Sentiment Agent
            symbol: Stock symbol
            current_time: Current time for reference (default: now)
        
        Returns:
            Dictionary with aggregated sentiment:
            {
                "aggregated_sentiment": float,
                "sentiment_label": str,
                "confidence": float,
                "news_count": int,
                "time_weighted": bool,
                "weights_applied": List[float]
            }
        
        Algorithm:
            1. For each sentiment score, calculate time weight
            2. Weight sentiment score by time weight
            3. Weight confidence by time weight
            4. Calculate weighted average sentiment
            5. Calculate weighted average confidence
            6. Determine sentiment label
        
        Example:
            aggregated = aggregator.aggregate(sentiment_scores, "AAPL")
            # Returns: {"aggregated_sentiment": 0.68, "sentiment_label": "positive", ...}
        """
        if not sentiment_scores:
            return {
                "aggregated_sentiment": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "news_count": 0,
                "time_weighted": True,
                "weights_applied": []
            }
        
        if current_time is None:
            from datetime import timezone
            current_time = datetime.now(timezone.utc)
        # Ensure timezone-aware
        if current_time.tzinfo is None:
            from datetime import timezone
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        # Calculate weights and weighted scores
        weighted_sentiments = []
        weighted_confidences = []
        weights = []
        
        for score in sentiment_scores:
            # Get article time (from processed_at or article metadata)
            processed_at = score.get("processed_at")
            if not processed_at:
                # Try to get from article if available
                article = score.get("article", {})
                processed_at = article.get("published_at") or article.get("processed_at")
            
            if processed_at:
                article_time = self._parse_datetime(processed_at)
                weight = self._calculate_time_weight(article_time, current_time)
            else:
                # If no time available, use default weight (recent)
                weight = 1.0
            
            sentiment_score = score.get("sentiment_score", 0.0)
            confidence = score.get("confidence", 0.7)
            
            # Apply weights
            weighted_sentiments.append(sentiment_score * weight)
            weighted_confidences.append(confidence * weight)
            weights.append(weight)
        
        # Calculate weighted averages
        total_weight = sum(weights)
        if total_weight == 0:
            # Fallback to simple average if no weights
            aggregated_sentiment = sum(s.get("sentiment_score", 0.0) for s in sentiment_scores) / len(sentiment_scores)
            aggregated_confidence = sum(s.get("confidence", 0.7) for s in sentiment_scores) / len(sentiment_scores)
        else:
            aggregated_sentiment = sum(weighted_sentiments) / total_weight
            aggregated_confidence = sum(weighted_confidences) / total_weight
        
        # Determine sentiment label
        if aggregated_sentiment > 0.3:
            sentiment_label = "positive"
        elif aggregated_sentiment < -0.3:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        return {
            "aggregated_sentiment": float(aggregated_sentiment),
            "sentiment_label": sentiment_label,
            "confidence": float(aggregated_confidence),
            "news_count": len(sentiment_scores),
            "time_weighted": True,
            "weights_applied": weights,
            "total_weight": float(total_weight)
        }
    
    def aggregate_simple(self, sentiment_scores: List[Dict[str, Any]], symbol: str) -> Dict[str, Any]:
        """
        Simple aggregation without time weighting (for comparison).
        
        Args:
            sentiment_scores: List of sentiment scores
            symbol: Stock symbol
        
        Returns:
            Dictionary with aggregated sentiment (simple average)
        
        Example:
            aggregated = aggregator.aggregate_simple(sentiment_scores, "AAPL")
        """
        if not sentiment_scores:
            return {
                "aggregated_sentiment": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "news_count": 0,
                "time_weighted": False
            }
        
        # Simple average
        sentiments = [s.get("sentiment_score", 0.0) for s in sentiment_scores]
        confidences = [s.get("confidence", 0.7) for s in sentiment_scores]
        
        aggregated_sentiment = sum(sentiments) / len(sentiments)
        aggregated_confidence = sum(confidences) / len(confidences)
        
        # Determine sentiment label
        if aggregated_sentiment > 0.3:
            sentiment_label = "positive"
        elif aggregated_sentiment < -0.3:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        return {
            "aggregated_sentiment": float(aggregated_sentiment),
            "sentiment_label": sentiment_label,
            "confidence": float(aggregated_confidence),
            "news_count": len(sentiment_scores),
            "time_weighted": False
        }

