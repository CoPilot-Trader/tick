"""
Full Pipeline Test: News Fetch → LLM Sentiment → Sentiment Aggregator

Tests the complete pipeline for all three Developer 1 agents.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.llm_sentiment_agent.agent import LLMSentimentAgent
from agents.sentiment_aggregator.agent import SentimentAggregator


def test_full_pipeline():
    """Test complete pipeline: News Fetch → LLM Sentiment → Aggregator."""
    print("\n" + "="*70)
    print("FULL PIPELINE TEST: News Fetch -> LLM Sentiment -> Sentiment Aggregator")
    print("="*70)
    
    # Initialize all agents
    print("\n[INIT] Initializing all agents...")
    news_agent = NewsFetchAgent(config={"use_mock_data": True})
    sentiment_agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": False})
    aggregator = SentimentAggregator(config={"use_time_weighting": True, "calculate_impact": True})
    
    news_agent.initialize()
    sentiment_agent.initialize()
    aggregator.initialize()
    
    print("[OK] All agents initialized")
    
    # Test with multiple tickers
    test_tickers = ["AAPL", "MSFT"]
    
    for ticker in test_tickers:
        print(f"\n{'='*70}")
        print(f"PROCESSING: {ticker}")
        print(f"{'='*70}")
        
        # Step 1: Fetch news
        print(f"\n[STEP 1] Fetching news for {ticker}...")
        news_result = news_agent.process(ticker, params={"limit": 5, "min_relevance": 0.3})
        articles = news_result.get("articles", [])
        print(f"[OK] Fetched {len(articles)} articles")
        
        if not articles:
            print(f"[SKIP] No articles for {ticker}, skipping...")
            continue
        
        # Step 2: Analyze sentiment
        print(f"\n[STEP 2] Analyzing sentiment for {ticker}...")
        sentiment_result = sentiment_agent.process(ticker, params={"articles": articles})
        sentiment_scores = sentiment_result.get("sentiment_scores", [])
        print(f"[OK] Analyzed {len(sentiment_scores)} articles")
        
        if sentiment_scores:
            avg_sentiment = sum(s.get("sentiment_score", 0.0) for s in sentiment_scores) / len(sentiment_scores)
            print(f"[OK] Average sentiment: {avg_sentiment:.2f}")
        
        # Step 3: Aggregate sentiment
        print(f"\n[STEP 3] Aggregating sentiment for {ticker}...")
        aggregated_result = aggregator.process(ticker, params={"sentiment_scores": sentiment_scores})
        
        print(f"[OK] Aggregated sentiment: {aggregated_result.get('aggregated_sentiment', 0.0):.2f}")
        print(f"[OK] Sentiment label: {aggregated_result.get('sentiment_label', 'unknown')}")
        print(f"[OK] Confidence: {aggregated_result.get('confidence', 0.0):.2f}")
        print(f"[OK] Impact: {aggregated_result.get('impact', 'unknown')}")
        print(f"[OK] News count: {aggregated_result.get('news_count', 0)}")
        print(f"[OK] Time weighted: {aggregated_result.get('time_weighted', False)}")
        print(f"[OK] Status: {aggregated_result.get('status', 'unknown')}")
    
    print(f"\n{'='*70}")
    print("[SUCCESS] Full pipeline test completed!")
    print(f"{'='*70}")
    return True


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)

