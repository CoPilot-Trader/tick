"""
MOD10: Sentiment Context Module

Provides ticker-level sentiment from news and social sources.

Output columns (prefix: sent_):
- news_sentiment_score: Aggregate news sentiment (-1 to 1)
- news_volume_24h: Number of news articles in last 24h
- sentiment_momentum: Change in sentiment over time
- social_buzz_score: Social media mention volume (normalized)
- analyst_sentiment: Analyst rating sentiment
- sentiment_divergence: Price vs sentiment divergence signal
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SentimentContext:
    """
    Ticker-level sentiment context module.

    Uses Alpha Vantage News Sentiment API.
    """

    def __init__(self):
        self._av_collector = None
        self._cached_sentiment: Dict[str, pd.DataFrame] = {}

    def _get_av_collector(self):
        """Lazy-load Alpha Vantage collector."""
        if self._av_collector is None:
            try:
                from ..collectors import AlphaVantageCollector
                self._av_collector = AlphaVantageCollector()
                self._av_collector.initialize()
            except Exception as e:
                logger.warning(f"Could not initialize Alpha Vantage collector: {e}")
        return self._av_collector

    def _calculate_sentiment_momentum(
        self,
        current_sentiment: float,
        previous_sentiment: Optional[float],
    ) -> float:
        """Calculate sentiment momentum (change over time)."""
        if previous_sentiment is None:
            return 0.0
        return current_sentiment - previous_sentiment

    def _calculate_sentiment_divergence(
        self,
        sentiment: float,
        price_change_pct: Optional[float],
    ) -> float:
        """
        Calculate divergence between sentiment and price.

        Positive divergence: Sentiment positive but price falling (potential buy)
        Negative divergence: Sentiment negative but price rising (potential sell)
        """
        if price_change_pct is None:
            return 0.0

        # Normalize price change to -1 to 1 scale (assume +/-10% is max)
        price_signal = np.clip(price_change_pct / 10, -1, 1)

        # Divergence = sentiment - price_signal
        # If both positive or both negative, low divergence
        # If opposite signs, high divergence
        divergence = sentiment - price_signal

        return divergence

    def get_context(
        self,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Get sentiment context for tickers.

        Args:
            date: Date for context (defaults to today)
            tickers: List of tickers to get sentiment for

        Returns:
            DataFrame with columns:
            - ticker, timestamp, news_sentiment_score, news_volume_24h,
              sentiment_momentum, social_buzz_score, analyst_sentiment,
              sentiment_divergence
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if tickers is None or len(tickers) == 0:
            logger.warning("No tickers provided for sentiment context")
            return pd.DataFrame()

        current_date = datetime.strptime(date, "%Y-%m-%d")
        rows = []

        av = self._get_av_collector()

        for ticker in tickers:
            row = {
                "ticker": ticker.upper(),
                "timestamp": current_date,
                "news_sentiment_score": 0.0,
                "news_volume_24h": 0,
                "sentiment_momentum": 0.0,
                "social_buzz_score": 0.0,
                "analyst_sentiment": 0.0,
                "sentiment_divergence": 0.0,
            }

            if av:
                try:
                    # Try to get news sentiment from Alpha Vantage
                    # Note: This requires the NEWS_SENTIMENT function which may have rate limits
                    sentiment_data = self._fetch_ticker_sentiment(ticker, av)
                    if sentiment_data:
                        row.update(sentiment_data)
                except Exception as e:
                    logger.debug(f"Could not fetch sentiment for {ticker}: {e}")

            rows.append(row)

        return pd.DataFrame(rows)

    def _fetch_ticker_sentiment(
        self,
        ticker: str,
        av_collector,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch sentiment data for a single ticker.

        Note: Alpha Vantage News Sentiment API requires premium access.
        This is a placeholder that returns simulated data.
        """
        # In production, would call:
        # av_collector.fetch_news_sentiment(ticker)

        # For now, return neutral sentiment as placeholder
        # Real implementation would parse news API response

        return {
            "news_sentiment_score": 0.0,
            "news_volume_24h": 0,
            "sentiment_momentum": 0.0,
            "social_buzz_score": 0.0,
            "analyst_sentiment": 0.0,
            "sentiment_divergence": 0.0,
        }

    def get_bulk_sentiment(
        self,
        tickers: List[str],
        date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get sentiment for multiple tickers efficiently.

        Uses batch API calls where possible.
        """
        return self.get_context(date=date, tickers=tickers)
