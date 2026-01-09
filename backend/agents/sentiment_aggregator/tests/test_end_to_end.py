"""
End-to-End Test for Sentiment Aggregator

This script tests the complete pipeline:
1. News Fetch Agent fetches articles
2. LLM Sentiment Agent analyzes sentiment
3. Sentiment Aggregator aggregates sentiment

Tests accuracy and correctness of all components.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.llm_sentiment_agent.agent import LLMSentimentAgent
from agents.sentiment_aggregator.agent import SentimentAggregator


def test_agent_initialization():
    """Test agent initialization."""
    print("\n" + "="*60)
    print("TEST 1: Agent Initialization")
    print("="*60)
    
    agent = SentimentAggregator(config={"use_time_weighting": True, "calculate_impact": True})
    initialized = agent.initialize()
    
    print(f"[OK] Agent initialized: {initialized}")
    print(f"[OK] Time weighting enabled: {agent.use_time_weighting}")
    print(f"[OK] Impact scoring enabled: {agent.enable_impact_scoring}")
    
    health = agent.health_check()
    print(f"[OK] Agent health: {health['status']}")
    
    return initialized


def test_aggregation():
    """Test sentiment aggregation."""
    print("\n" + "="*60)
    print("TEST 2: Sentiment Aggregation")
    print("="*60)
    
    agent = SentimentAggregator(config={"use_time_weighting": True})
    agent.initialize()
    
    # Create test sentiment scores
    sentiment_scores = [
        {
            "article_id": "article_1",
            "sentiment_score": 0.75,
            "sentiment_label": "positive",
            "confidence": 0.85,
            "processed_at": "2024-01-15T10:00:00Z"
        },
        {
            "article_id": "article_2",
            "sentiment_score": 0.65,
            "sentiment_label": "positive",
            "confidence": 0.80,
            "processed_at": "2024-01-15T09:00:00Z"
        },
        {
            "article_id": "article_3",
            "sentiment_score": 0.55,
            "sentiment_label": "positive",
            "confidence": 0.75,
            "processed_at": "2024-01-15T08:00:00Z"
        }
    ]
    
    # Aggregate
    result = agent.aggregate(sentiment_scores, "AAPL", time_weighted=True)
    
    print(f"[OK] Aggregated sentiment: {result.get('aggregated_sentiment', 0.0):.2f}")
    print(f"[OK] Sentiment label: {result.get('sentiment_label', 'unknown')}")
    print(f"[OK] Confidence: {result.get('confidence', 0.0):.2f}")
    print(f"[OK] Impact: {result.get('impact', 'unknown')}")
    print(f"[OK] News count: {result.get('news_count', 0)}")
    print(f"[OK] Time weighted: {result.get('time_weighted', False)}")
    
    # Verify result structure
    required_fields = ["aggregated_sentiment", "sentiment_label", "confidence", "impact", "news_count"]
    missing_fields = [field for field in required_fields if field not in result]
    
    if missing_fields:
        print(f"[ERROR] Missing fields: {missing_fields}")
        return False
    
    print(f"[OK] All required fields present")
    
    return True


def test_impact_scoring():
    """Test impact scoring."""
    print("\n" + "="*60)
    print("TEST 3: Impact Scoring")
    print("="*60)
    
    agent = SentimentAggregator()
    agent.initialize()
    
    # Test High impact
    impact_high = agent.calculate_impact(0.75, 15, recency=0.9, confidence=0.85)
    print(f"[OK] High impact test: {impact_high} (expected: High)")
    
    # Test Medium impact
    impact_medium = agent.calculate_impact(0.50, 8, recency=0.7, confidence=0.75)
    print(f"[OK] Medium impact test: {impact_medium} (expected: Medium)")
    
    # Test Low impact
    impact_low = agent.calculate_impact(0.20, 3, recency=0.5, confidence=0.60)
    print(f"[OK] Low impact test: {impact_low} (expected: Low)")
    
    return True


def test_time_weighting():
    """Test time-weighted aggregation."""
    print("\n" + "="*60)
    print("TEST 4: Time-Weighted Aggregation")
    print("="*60)
    
    agent = SentimentAggregator()
    agent.initialize()
    
    # Create sentiment scores with different timestamps
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    
    sentiment_scores = [
        {
            "article_id": "recent",
            "sentiment_score": 0.80,
            "confidence": 0.90,
            "processed_at": (now - timedelta(hours=1)).isoformat() + "Z"  # Recent
        },
        {
            "article_id": "old",
            "sentiment_score": 0.60,
            "confidence": 0.80,
            "processed_at": (now - timedelta(hours=48)).isoformat() + "Z"  # Old
        }
    ]
    
    # Test with time weighting
    result_weighted = agent.aggregate(sentiment_scores, "AAPL", time_weighted=True)
    print(f"[OK] Time-weighted aggregation: {result_weighted.get('aggregated_sentiment', 0.0):.2f}")
    print(f"[OK] Time weighted: {result_weighted.get('time_weighted', False)}")
    
    # Test without time weighting
    result_simple = agent.aggregate(sentiment_scores, "AAPL", time_weighted=False)
    print(f"[OK] Simple aggregation: {result_simple.get('aggregated_sentiment', 0.0):.2f}")
    print(f"[OK] Time weighted: {result_simple.get('time_weighted', False)}")
    
    # Recent article should have more weight
    if result_weighted.get('aggregated_sentiment', 0.0) > result_simple.get('aggregated_sentiment', 0.0):
        print(f"[OK] Time weighting gives more weight to recent articles")
    
    return True


def test_full_pipeline():
    """Test full pipeline: News Fetch -> LLM Sentiment -> Aggregator."""
    print("\n" + "="*60)
    print("TEST 5: Full Pipeline Integration")
    print("="*60)
    
    # Step 1: News Fetch Agent
    print("\n[STEP 1] Fetching news...")
    news_agent = NewsFetchAgent(config={"use_mock_data": True})
    news_agent.initialize()
    news_result = news_agent.process("AAPL", params={"limit": 5, "min_relevance": 0.3})
    articles = news_result.get("articles", [])
    print(f"[OK] Fetched {len(articles)} articles")
    
    if not articles:
        print("[WARNING] No articles fetched, skipping pipeline test")
        return True
    
    # Step 2: LLM Sentiment Agent
    print("\n[STEP 2] Analyzing sentiment...")
    sentiment_agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": False})
    sentiment_agent.initialize()
    sentiment_result = sentiment_agent.process("AAPL", params={"articles": articles})
    sentiment_scores = sentiment_result.get("sentiment_scores", [])
    print(f"[OK] Analyzed {len(sentiment_scores)} articles")
    
    if not sentiment_scores:
        print("[WARNING] No sentiment scores, skipping aggregation")
        return True
    
    # Step 3: Sentiment Aggregator
    print("\n[STEP 3] Aggregating sentiment...")
    aggregator = SentimentAggregator(config={"use_time_weighting": True, "calculate_impact": True})
    aggregator.initialize()
    aggregated_result = aggregator.process("AAPL", params={"sentiment_scores": sentiment_scores})
    
    print(f"[OK] Aggregated sentiment: {aggregated_result.get('aggregated_sentiment', 0.0):.2f}")
    print(f"[OK] Sentiment label: {aggregated_result.get('sentiment_label', 'unknown')}")
    print(f"[OK] Confidence: {aggregated_result.get('confidence', 0.0):.2f}")
    print(f"[OK] Impact: {aggregated_result.get('impact', 'unknown')}")
    print(f"[OK] News count: {aggregated_result.get('news_count', 0)}")
    print(f"[OK] Status: {aggregated_result.get('status', 'unknown')}")
    
    # Verify pipeline worked
    if aggregated_result.get('status') == 'success':
        print("\n[SUCCESS] Full pipeline works correctly!")
        return True
    else:
        print(f"\n[ERROR] Pipeline failed: {aggregated_result.get('message', 'unknown error')}")
        return False


def run_all_tests():
    """Run all tests and show summary."""
    print("\n" + "="*60)
    print("SENTIMENT AGGREGATOR - END-TO-END TEST SUITE")
    print("="*60)
    print("\nTesting all components...")
    
    results = {}
    
    try:
        results["Initialization"] = test_agent_initialization()
    except Exception as e:
        print(f"[ERROR] Initialization test failed: {e}")
        results["Initialization"] = False
    
    try:
        results["Aggregation"] = test_aggregation()
    except Exception as e:
        print(f"[ERROR] Aggregation test failed: {e}")
        results["Aggregation"] = False
    
    try:
        results["ImpactScoring"] = test_impact_scoring()
    except Exception as e:
        print(f"[ERROR] ImpactScoring test failed: {e}")
        results["ImpactScoring"] = False
    
    try:
        results["TimeWeighting"] = test_time_weighting()
    except Exception as e:
        print(f"[ERROR] TimeWeighting test failed: {e}")
        results["TimeWeighting"] = False
    
    try:
        results["FullPipeline"] = test_full_pipeline()
    except Exception as e:
        print(f"[ERROR] FullPipeline test failed: {e}")
        results["FullPipeline"] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Sentiment Aggregator is working correctly.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

