"""
Impact Scorer

This module provides impact scoring for aggregated sentiment.
Determines if sentiment impact is High, Medium, or Low based on:
- Sentiment strength (how positive/negative)
- News volume (number of articles)
- Recency (how recent the news is)

Why Impact Scoring?
- Helps Fusion Agent prioritize signals
- Identifies significant sentiment shifts
- Filters out noise from low-impact sentiment
"""

from typing import Dict, Any, Optional


class ImpactScorer:
    """
    Impact scorer for aggregated sentiment.
    
    Calculates impact level (High/Medium/Low) based on:
    - Sentiment strength
    - News volume
    - Recency
    
    Example:
        scorer = ImpactScorer()
        impact = scorer.calculate_impact(aggregated_sentiment=0.75, news_count=15, recency=0.9)
        # Returns: "High"
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize impact scorer.
        
        Args:
            config: Optional configuration:
                   - high_impact_threshold: Minimum score for High impact (default: 0.7)
                   - medium_impact_threshold: Minimum score for Medium impact (default: 0.4)
                   - min_news_count_high: Minimum news count for High impact (default: 10)
                   - min_news_count_medium: Minimum news count for Medium impact (default: 5)
        """
        self.config = config or {}
        self.high_threshold = self.config.get("high_impact_threshold", 0.7)
        self.medium_threshold = self.config.get("medium_impact_threshold", 0.4)
        self.min_news_high = self.config.get("min_news_count_high", 10)
        self.min_news_medium = self.config.get("min_news_count_medium", 5)
    
    def calculate_impact(
        self,
        aggregated_sentiment: float,
        news_count: int,
        recency: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> str:
        """
        Calculate impact score (High/Medium/Low).
        
        Args:
            aggregated_sentiment: Aggregated sentiment score (-1.0 to +1.0)
            news_count: Number of news articles
            recency: Recency score (0.0 to 1.0) - optional
            confidence: Confidence score (0.0 to 1.0) - optional
        
        Returns:
            Impact level: "High", "Medium", or "Low"
        
        Algorithm:
            1. Calculate sentiment strength (absolute value)
            2. Consider news volume
            3. Consider recency (if provided)
            4. Consider confidence (if provided)
            5. Combine factors to determine impact
        
        Example:
            impact = scorer.calculate_impact(0.75, 15, recency=0.9, confidence=0.85)
            # Returns: "High"
        """
        # Calculate sentiment strength (absolute value)
        sentiment_strength = abs(aggregated_sentiment)
        
        # Base impact score (0.0 to 1.0)
        impact_score = 0.0
        
        # Factor 1: Sentiment strength (40% weight)
        impact_score += sentiment_strength * 0.4
        
        # Factor 2: News volume (30% weight)
        # More news = higher impact (up to a point)
        volume_score = min(news_count / 20.0, 1.0)  # Cap at 20 articles
        impact_score += volume_score * 0.3
        
        # Factor 3: Recency (20% weight, if provided)
        if recency is not None:
            impact_score += recency * 0.2
        else:
            # Assume recent if not provided
            impact_score += 0.15  # Default recency contribution
        
        # Factor 4: Confidence (10% weight, if provided)
        if confidence is not None:
            impact_score += confidence * 0.1
        else:
            # Assume medium confidence if not provided
            impact_score += 0.05  # Default confidence contribution
        
        # Determine impact level
        if impact_score >= self.high_threshold and news_count >= self.min_news_high:
            return "High"
        elif impact_score >= self.medium_threshold and news_count >= self.min_news_medium:
            return "Medium"
        else:
            return "Low"
    
    def calculate_impact_simple(self, aggregated_sentiment: float, news_count: int) -> str:
        """
        Simple impact calculation (without recency/confidence).
        
        Args:
            aggregated_sentiment: Aggregated sentiment score
            news_count: Number of news articles
        
        Returns:
            Impact level: "High", "Medium", or "Low"
        
        Example:
            impact = scorer.calculate_impact_simple(0.75, 15)
            # Returns: "High"
        """
        sentiment_strength = abs(aggregated_sentiment)
        
        # High impact: strong sentiment + many articles
        if sentiment_strength >= 0.6 and news_count >= 10:
            return "High"
        
        # Medium impact: moderate sentiment + some articles
        if sentiment_strength >= 0.4 and news_count >= 5:
            return "Medium"
        
        # Low impact: everything else
        return "Low"
    
    def calculate_recency_score(self, weights: list[float]) -> float:
        """
        Calculate recency score from time weights.
        
        Args:
            weights: List of time weights (0.0 to 1.0)
        
        Returns:
            Recency score (0.0 to 1.0)
            1.0 = All articles are very recent
            0.0 = All articles are very old
        
        Example:
            recency = scorer.calculate_recency_score([0.9, 0.8, 0.7])
            # Returns: 0.8 (average weight)
        """
        if not weights:
            return 0.0
        
        return sum(weights) / len(weights)

