"""
Quick Integration Test: News Fetch Agent → LLM Sentiment Agent

Tests the integration between News Fetch Agent and LLM Sentiment Agent.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.llm_sentiment_agent.agent import LLMSentimentAgent


def test_integration():
    """Test integration between News Fetch and LLM Sentiment agents."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: News Fetch -> LLM Sentiment")
    print("="*60)
    
    # Step 1: Initialize News Fetch Agent
    print("\n[STEP 1] Initializing News Fetch Agent...")
    news_agent = NewsFetchAgent(config={"use_mock_data": True})
    news_initialized = news_agent.initialize()
    print(f"[OK] News Fetch Agent initialized: {news_initialized}")
    
    # Step 2: Fetch news for AAPL
    print("\n[STEP 2] Fetching news for AAPL...")
    news_result = news_agent.process("AAPL", params={"limit": 5, "min_relevance": 0.3})
    articles = news_result.get("articles", [])
    print(f"[OK] Fetched {len(articles)} articles")
    
    if not articles:
        print("[WARNING] No articles fetched. Integration test cannot proceed.")
        return False
    
    # Step 3: Initialize LLM Sentiment Agent
    print("\n[STEP 3] Initializing LLM Sentiment Agent...")
    sentiment_agent = LLMSentimentAgent(config={
        "use_mock_data": True,
        "use_cache": False  # Disable cache for this test (avoids sentence-transformers dependency)
    })
    sentiment_initialized = sentiment_agent.initialize()
    print(f"[OK] LLM Sentiment Agent initialized: {sentiment_initialized}")
    
    # Step 4: Analyze sentiment
    print("\n[STEP 4] Analyzing sentiment for articles...")
    sentiment_result = sentiment_agent.process("AAPL", params={"articles": articles})
    
    sentiment_scores = sentiment_result.get("sentiment_scores", [])
    print(f"[OK] Analyzed {len(sentiment_scores)} articles")
    print(f"[OK] Status: {sentiment_result.get('status', 'unknown')}")
    
    # Step 5: Verify results
    print("\n[STEP 5] Verifying results...")
    if len(sentiment_scores) != len(articles):
        print(f"[ERROR] Mismatch: {len(sentiment_scores)} scores for {len(articles)} articles")
        return False
    
    print(f"[OK] All articles have sentiment scores")
    
    # Show sample results
    print("\n[OK] Sample results:")
    for i, score in enumerate(sentiment_scores[:3], 1):
        print(f"  {i}. Article ID: {score.get('article_id', 'unknown')}")
        print(f"     Sentiment: {score.get('sentiment_score', 0.0):.2f} ({score.get('sentiment_label', 'unknown')})")
        print(f"     Confidence: {score.get('confidence', 0.0):.2f}")
        print(f"     Cached: {score.get('cached', False)}")
    
    # Calculate average sentiment
    if sentiment_scores:
        avg_sentiment = sum(s.get("sentiment_score", 0.0) for s in sentiment_scores) / len(sentiment_scores)
        print(f"\n[OK] Average sentiment score: {avg_sentiment:.2f}")
    
    print("\n[SUCCESS] Integration test passed! Agents work together correctly.")
    return True


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)

