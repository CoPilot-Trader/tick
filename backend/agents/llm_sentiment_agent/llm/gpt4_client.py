"""
GPT-4 Client for OpenAI API

This module provides integration with OpenAI GPT-4 API for sentiment analysis.

OpenAI GPT-4 API:
- High-quality sentiment analysis
- Requires API key
- Pay-per-use pricing
- Rate limits apply

API Documentation: https://platform.openai.com/docs/api-reference

Why GPT-4?
- Superior sentiment analysis quality
- Understands financial context
- Handles nuanced language
- Provides reasoning for sentiment
"""

import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class GPT4Client:
    """
    Client for OpenAI GPT-4 API.
    
    This client makes API calls to OpenAI GPT-4 and extracts sentiment
    scores from the responses.
    
    Example:
        client = GPT4Client(config={"api_key": "your_key"})
        response = client.analyze_sentiment(article, "AAPL")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize GPT-4 client.
        
        Args:
            config: Configuration dictionary:
                   - api_key: OpenAI API key (required)
                   - model: Model name (default: "gpt-4")
                   - temperature: Temperature for generation (default: 0.3)
                   - max_tokens: Maximum tokens in response (default: 200)
                   - timeout: Request timeout in seconds (default: 30)
        """
        self.config = config or {}
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("OpenAI API key is required in config")
        
        self.model = self.config.get("model", "gpt-4")
        self.temperature = self.config.get("temperature", 0.3)
        self.max_tokens = self.config.get("max_tokens", 200)
        self.timeout = self.config.get("timeout", 30)
        
        # Initialize OpenAI client (will be imported when needed)
        self._client = None
    
    def _get_client(self):
        """
        Get or create OpenAI client.
        
        Returns:
            OpenAI client instance
        
        Raises:
            ImportError: If openai package is not installed
        """
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package is required. Install with: pip install openai"
                )
        
        return self._client
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse GPT-4 response and extract sentiment data.
        
        Args:
            response_text: Raw response text from GPT-4
        
        Returns:
            Dictionary with sentiment score, label, confidence, reasoning
        
        Raises:
            ValueError: If response cannot be parsed
        """
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {
                    "sentiment_score": float(parsed.get("sentiment_score", 0.0)),
                    "sentiment_label": parsed.get("sentiment_label", "neutral"),
                    "confidence": float(parsed.get("confidence", 0.7)),
                    "reasoning": parsed.get("reasoning", "")
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                raise ValueError(f"Failed to parse GPT-4 response: {e}")
        
        # Fallback: Try to extract sentiment score from text
        score_match = re.search(r'"sentiment_score":\s*([-+]?\d*\.?\d+)', response_text)
        if score_match:
            score = float(score_match.group(1))
            return {
                "sentiment_score": score,
                "sentiment_label": "positive" if score > 0.3 else ("negative" if score < -0.3 else "neutral"),
                "confidence": 0.6,
                "reasoning": "Extracted from response text"
            }
        
        raise ValueError("Could not parse sentiment from GPT-4 response")
    
    def analyze_sentiment(self, article: Dict[str, Any], symbol: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze sentiment for an article using GPT-4.

        Args:
            article: News article dictionary
            symbol: Stock symbol
            prompt: Optional formatted prompt (if not provided, will be generated)

        Returns:
            Dictionary with sentiment analysis result
        """
        try:
            client = self._get_client()

            title = article.get("title", "")
            content = article.get("content", article.get("summary", title))

            if not prompt:
                prompt = (
                    f"Analyze the sentiment of this financial news article about {symbol}.\n\n"
                    f"Title: {title}\n"
                    f"Content: {content[:1500]}\n\n"
                    "Respond ONLY with a JSON object (no markdown, no extra text):\n"
                    '{"sentiment_score": <float -1.0 to 1.0>, '
                    '"sentiment_label": "<positive|neutral|negative>", '
                    '"confidence": <float 0.0 to 1.0>, '
                    '"reasoning": "<brief explanation>"}'
                )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial sentiment analyst. Analyze stock market news "
                            "and return sentiment scores as JSON. Be precise and concise."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            response_text = response.choices[0].message.content
            parsed = self._parse_response(response_text)

            return {
                "sentiment_score": parsed["sentiment_score"],
                "sentiment_label": parsed["sentiment_label"],
                "confidence": parsed["confidence"],
                "reasoning": parsed.get("reasoning", ""),
                "model": self.model,
                "cached": False,
                "processed_at": datetime.utcnow().isoformat() + "Z",
            }

        except ImportError:
            raise
        except Exception as e:
            raise ConnectionError(f"GPT-4 API error: {str(e)}")
    
    def batch_analyze_sentiment(self, articles: List[Dict[str, Any]], symbol: str, prompts: List[str]) -> List[Dict[str, Any]]:
        """
        Batch analyze sentiment for multiple articles.

        Args:
            articles: List of news articles
            symbol: Stock symbol
            prompts: List of formatted prompts

        Returns:
            List of sentiment analysis results
        """
        results = []
        for article, prompt in zip(articles, prompts):
            try:
                result = self.analyze_sentiment(article, symbol, prompt=prompt)
                results.append(result)
            except Exception as e:
                results.append({
                    "sentiment_score": 0.0,
                    "sentiment_label": "neutral",
                    "confidence": 0.0,
                    "reasoning": f"Error: {str(e)}",
                    "model": self.model,
                    "cached": False,
                    "processed_at": datetime.utcnow().isoformat() + "Z",
                })
        return results

