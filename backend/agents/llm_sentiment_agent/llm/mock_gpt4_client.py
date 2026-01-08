"""
Mock GPT-4 Client for Testing

This module provides a mock GPT-4 client that returns predefined responses
without making actual API calls. Used for testing and development.

Why Mock Client?
- Test without OpenAI API dependencies
- No API costs during development
- Predictable test results
- Fast test execution
- Test error scenarios easily
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class MockGPT4Client:
    """
    Mock GPT-4 client that returns predefined responses.
    
    This client loads mock responses from a JSON file and returns them
    based on article content similarity or article ID matching.
    
    Example:
        client = MockGPT4Client()
        response = client.analyze_sentiment(article, "AAPL")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock GPT-4 client.
        
        Args:
            config: Optional configuration:
                   - mock_data_path: Path to mock responses JSON file
                   - simulate_delay: Simulate API delay in seconds (default: 0.1)
                   - simulate_errors: Simulate API errors (default: False)
        """
        self.config = config or {}
        self.mock_data_path = self.config.get(
            "mock_data_path",
            Path(__file__).parent.parent / "tests" / "mocks" / "gpt4_mock_responses.json"
        )
        self.simulate_delay = self.config.get("simulate_delay", 0.1)
        self.simulate_errors = self.config.get("simulate_errors", False)
        self._mock_responses = None
        self._call_count = 0
    
    def _load_mock_responses(self) -> Dict[str, Any]:
        """
        Load mock responses from JSON file.
        
        Returns:
            Dictionary mapping article IDs or content hashes to responses
        
        Raises:
            FileNotFoundError: If mock data file doesn't exist
            json.JSONDecodeError: If JSON file is invalid
        """
        if self._mock_responses is None:
            if not self.mock_data_path.exists():
                # Return default mock responses if file doesn't exist
                return self._get_default_responses()
            
            with open(self.mock_data_path, 'r', encoding='utf-8') as f:
                self._mock_responses = json.load(f)
        
        return self._mock_responses
    
    def _get_default_responses(self) -> Dict[str, Any]:
        """
        Get default mock responses if file doesn't exist.
        
        Returns:
            Dictionary with default mock responses
        """
        return {
            "default": {
                "sentiment_score": 0.5,
                "sentiment_label": "neutral",
                "confidence": 0.7,
                "reasoning": "Default mock response"
            }
        }
    
    def _find_mock_response(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find mock response for an article.
        
        First tries to match by article ID, then by content hash.
        If no match found, generates sentiment from article content.
        
        Args:
            article: News article dictionary
        
        Returns:
            Mock response dictionary or None
        """
        mock_data = self._load_mock_responses()
        
        # Try to match by article ID
        article_id = article.get("id", "")
        if article_id and article_id in mock_data:
            return mock_data[article_id]
        
        # Try to match by title (simple hash)
        title = article.get("title", "")
        if title:
            title_hash = str(hash(title))[:10]
            if title_hash in mock_data:
                return mock_data[title_hash]
        
        # If no exact match, generate sentiment from content
        return self._generate_sentiment_from_content(article)
    
    def _generate_sentiment_from_content(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate sentiment score from article content analysis.
        
        Analyzes article title and content for positive/negative indicators
        and generates a realistic sentiment score.
        
        Args:
            article: News article dictionary
        
        Returns:
            Dictionary with generated sentiment analysis:
            {
                "sentiment_score": float,
                "sentiment_label": str,
                "confidence": float,
                "reasoning": str
            }
        """
        # Get article text
        title = article.get("title", "").lower()
        content = (article.get("content", "") or article.get("summary", "")).lower()
        text = f"{title} {content}"
        
        # Positive indicators (strong)
        strong_positive = [
            "record", "surge", "soar", "jump", "spike", "rally", "boom",
            "exceed", "beat", "outperform", "strong", "growth", "increase", "rise",
            "profit", "earnings", "revenue", "success", "win", "gain", "upgrade",
            "breakthrough", "milestone", "achievement", "expansion", "launch"
        ]
        
        # Positive indicators (moderate)
        moderate_positive = [
            "positive", "improve", "better", "up", "higher", "boost",
            "partnership", "deal", "agreement", "investment", "develop", "progress"
        ]
        
        # Negative indicators (strong)
        strong_negative = [
            "decline", "drop", "fall", "plunge", "crash", "collapse", "loss",
            "miss", "disappoint", "fail", "lawsuit", "investigation", "scandal",
            "crisis", "concern", "worry", "threat", "risk", "down", "lower",
            "cut", "reduce", "layoff", "bankruptcy", "default", "breach"
        ]
        
        # Negative indicators (moderate)
        moderate_negative = [
            "negative", "worse", "weak", "slow", "struggle", "challenge",
            "pressure", "uncertainty", "volatility", "decline", "decrease"
        ]
        
        # Count matches
        strong_pos_count = sum(1 for word in strong_positive if word in text)
        moderate_pos_count = sum(1 for word in moderate_positive if word in text)
        strong_neg_count = sum(1 for word in strong_negative if word in text)
        moderate_neg_count = sum(1 for word in moderate_negative if word in text)
        
        # Calculate base sentiment score
        # Strong indicators are worth more
        positive_score = (strong_pos_count * 0.15) + (moderate_pos_count * 0.08)
        negative_score = (strong_neg_count * 0.15) + (moderate_neg_count * 0.08)
        
        # Net sentiment
        net_sentiment = positive_score - negative_score
        
        # Normalize to -1.0 to +1.0 range
        # Cap at reasonable bounds
        sentiment_score = max(-0.9, min(0.9, net_sentiment))
        
        # If no strong indicators, use a neutral range with slight bias
        if abs(sentiment_score) < 0.1:
            # Check for neutral/balanced content
            if positive_score > 0 or negative_score > 0:
                # Slight positive or negative bias
                sentiment_score = 0.15 if positive_score > negative_score else -0.15
            else:
                # Truly neutral
                sentiment_score = 0.0
        
        # Determine sentiment label
        if sentiment_score > 0.3:
            sentiment_label = "positive"
        elif sentiment_score < -0.3:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # Calculate confidence based on indicator strength
        total_indicators = strong_pos_count + moderate_pos_count + strong_neg_count + moderate_neg_count
        if total_indicators == 0:
            confidence = 0.5  # Low confidence if no clear indicators
        elif total_indicators >= 5:
            confidence = 0.85  # High confidence with many indicators
        else:
            confidence = 0.65 + (total_indicators * 0.04)  # Scale with indicators
        
        # Generate reasoning
        if sentiment_score > 0.5:
            reasoning = f"Article contains strong positive indicators (record, growth, success) indicating positive sentiment"
        elif sentiment_score > 0.2:
            reasoning = f"Article shows positive trends and improvements, indicating moderately positive sentiment"
        elif sentiment_score < -0.5:
            reasoning = f"Article contains strong negative indicators (decline, loss, crisis) indicating negative sentiment"
        elif sentiment_score < -0.2:
            reasoning = f"Article shows negative trends and challenges, indicating moderately negative sentiment"
        else:
            reasoning = f"Article shows balanced or neutral indicators, indicating neutral sentiment"
        
        return {
            "sentiment_score": round(sentiment_score, 2),
            "sentiment_label": sentiment_label,
            "confidence": round(confidence, 2),
            "reasoning": reasoning
        }
    
    def analyze_sentiment(self, article: Dict[str, Any], symbol: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze sentiment for an article (mock implementation).
        
        Args:
            article: News article dictionary
            symbol: Stock symbol
            prompt: Optional prompt (not used in mock, but matches real client signature)
        
        Returns:
            Dictionary with sentiment analysis result:
            {
                "sentiment_score": float,
                "sentiment_label": str,
                "confidence": float,
                "reasoning": str
            }
        
        Example:
            response = client.analyze_sentiment(article, "AAPL")
            # Returns: {"sentiment_score": 0.75, "sentiment_label": "positive", ...}
        """
        import time
        
        # Simulate API delay
        if self.simulate_delay > 0:
            time.sleep(self.simulate_delay)
        
        # Simulate errors if configured
        if self.simulate_errors and self._call_count % 10 == 0:
            raise Exception("Simulated API error")
        
        self._call_count += 1
        
        # Find mock response
        mock_response = self._find_mock_response(article)
        
        # Add metadata
        result = {
            "sentiment_score": mock_response.get("sentiment_score", 0.0),
            "sentiment_label": mock_response.get("sentiment_label", "neutral"),
            "confidence": mock_response.get("confidence", 0.7),
            "reasoning": mock_response.get("reasoning", "Mock response"),
            "model": "gpt-4-mock",
            "cached": False,
            "processed_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return result
    
    def batch_analyze_sentiment(self, articles: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
        """
        Batch analyze sentiment for multiple articles (mock implementation).
        
        Args:
            articles: List of news articles
            symbol: Stock symbol
        
        Returns:
            List of sentiment analysis results
        
        Example:
            responses = client.batch_analyze_sentiment(articles, "AAPL")
        """
        results = []
        for article in articles:
            result = self.analyze_sentiment(article, symbol)
            results.append(result)
        
        return results
    
    def get_call_count(self) -> int:
        """Get number of API calls made (for testing)."""
        return self._call_count
    
    def reset_call_count(self) -> None:
        """Reset call count (for testing)."""
        self._call_count = 0

