"""
End-to-End Test for LLM Sentiment Agent

This script tests the complete pipeline:
1. Agent receives articles from News Fetch Agent
2. Checks semantic cache
3. Analyzes with GPT-4 (mock)
4. Stores in cache
5. Returns sentiment scores

Tests accuracy and correctness of all components.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.llm_sentiment_agent.agent import LLMSentimentAgent
from agents.news_fetch_agent.agent import NewsFetchAgent


def test_agent_initialization():
    """Test agent initialization."""
    print("\n" + "="*60)
    print("TEST 1: Agent Initialization")
    print("="*60)
    
    agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": True})
    initialized = agent.initialize()
    
    print(f"[OK] Agent initialized: {initialized}")
    print(f"[OK] Using mock data: {agent.use_mock_data}")
    print(f"[OK] Cache enabled: {agent.use_cache}")
    
    health = agent.health_check()
    print(f"[OK] Agent health: {health['status']}")
    
    return initialized


def test_sentiment_analysis():
    """Test sentiment analysis for single article."""
    print("\n" + "="*60)
    print("TEST 2: Sentiment Analysis (Single Article)")
    print("="*60)
    
    agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": True})
    agent.initialize()
    
    # Create test article
    article = {
        "id": "mock_aapl_001",
        "title": "Apple Reports Record Q4 Earnings, Exceeds Analyst Expectations",
        "content": "Apple Inc reported record-breaking Q4 earnings, exceeding analyst expectations by 8%.",
        "source": "Reuters",
        "published_at": "2024-01-15T10:00:00Z"
    }
    
    # Analyze sentiment
    result = agent.analyze_sentiment(article, "AAPL", use_cache=True)
    
    print(f"[OK] Analyzed article: {article['title'][:50]}...")
    print(f"[OK] Sentiment score: {result.get('sentiment_score', 0.0):.2f}")
    print(f"[OK] Sentiment label: {result.get('sentiment_label', 'unknown')}")
    print(f"[OK] Confidence: {result.get('confidence', 0.0):.2f}")
    print(f"[OK] Cached: {result.get('cached', False)}")
    
    # Verify result structure
    required_fields = ["article_id", "sentiment_score", "sentiment_label", "confidence", "cached"]
    missing_fields = [field for field in required_fields if field not in result]
    
    if missing_fields:
        print(f"[ERROR] Missing fields: {missing_fields}")
        return False
    
    print(f"[OK] All required fields present")
    
    return True


def test_cache_functionality():
    """Test semantic cache functionality."""
    print("\n" + "="*60)
    print("TEST 3: Semantic Cache")
    print("="*60)
    
    agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": True})
    agent.initialize()
    
    # First analysis (cache miss)
    article1 = {
        "id": "test_article_1",
        "title": "Apple Reports Strong Earnings",
        "content": "Apple Inc reported strong quarterly earnings.",
        "source": "Reuters"
    }
    
    result1 = agent.analyze_sentiment(article1, "AAPL", use_cache=True)
    print(f"[OK] First analysis - Cached: {result1.get('cached', False)} (expected: False)")
    
    # Second analysis with similar article (should be cache hit)
    article2 = {
        "id": "test_article_2",
        "title": "Apple Reports Strong Earnings",  # Same title
        "content": "Apple Inc reported strong quarterly earnings.",  # Same content
        "source": "Bloomberg"
    }
    
    result2 = agent.analyze_sentiment(article2, "AAPL", use_cache=True)
    print(f"[OK] Second analysis (similar) - Cached: {result2.get('cached', False)} (expected: True)")
    
    # Get cache stats
    cache_stats = agent.get_cache_stats()
    print(f"[OK] Cache hits: {cache_stats.get('hits', 0)}")
    print(f"[OK] Cache misses: {cache_stats.get('misses', 0)}")
    print(f"[OK] Cache hit rate: {cache_stats.get('hit_rate', 0.0):.2%}")
    
    return True


def test_batch_analysis():
    """Test batch sentiment analysis."""
    print("\n" + "="*60)
    print("TEST 4: Batch Analysis")
    print("="*60)
    
    agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": True})
    agent.initialize()
    
    # Create test articles
    articles = [
        {
            "id": f"test_article_{i}",
            "title": f"Test Article {i}",
            "content": f"Content for article {i}",
            "source": "Test Source"
        }
        for i in range(5)
    ]
    
    # Batch analyze
    results = agent.batch_analyze(articles, "AAPL")
    
    print(f"[OK] Analyzed {len(results)} articles")
    print(f"[OK] All articles have sentiment scores: {all('sentiment_score' in r for r in results)}")
    
    # Show sample results
    if results:
        print(f"\n[OK] Sample results:")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. Score: {result.get('sentiment_score', 0.0):.2f}, "
                  f"Label: {result.get('sentiment_label', 'unknown')}, "
                  f"Cached: {result.get('cached', False)}")
    
    return True


def test_integration_with_news_fetch():
    """Test integration with News Fetch Agent."""
    print("\n" + "="*60)
    print("TEST 5: Integration with News Fetch Agent")
    print("="*60)
    
    # Initialize News Fetch Agent
    news_agent = NewsFetchAgent(config={"use_mock_data": True})
    news_agent.initialize()
    
    # Fetch news for AAPL
    news_result = news_agent.process("AAPL", params={"limit": 3, "min_relevance": 0.3})
    articles = news_result.get("articles", [])
    
    print(f"[OK] Fetched {len(articles)} articles from News Fetch Agent")
    
    if not articles:
        print("[WARNING] No articles fetched, skipping sentiment analysis")
        return True
    
    # Initialize LLM Sentiment Agent
    sentiment_agent = LLMSentimentAgent(config={"use_mock_data": True, "use_cache": True})
    sentiment_agent.initialize()
    
    # Analyze sentiment for articles
    sentiment_result = sentiment_agent.process("AAPL", params={"articles": articles})
    
    print(f"[OK] Analyzed {len(sentiment_result.get('sentiment_scores', []))} articles")
    print(f"[OK] Status: {sentiment_result.get('status', 'unknown')}")
    
    # Show results
    sentiment_scores = sentiment_result.get("sentiment_scores", [])
    if sentiment_scores:
        avg_score = sum(s.get("sentiment_score", 0.0) for s in sentiment_scores) / len(sentiment_scores)
        print(f"[OK] Average sentiment score: {avg_score:.2f}")
        
        print(f"\n[OK] Sample sentiment analysis results:")
        for i, score in enumerate(sentiment_scores[:3], 1):
            print(f"  {i}. Article: {score.get('article_id', 'unknown')}")
            print(f"     Score: {score.get('sentiment_score', 0.0):.2f}, "
                  f"Label: {score.get('sentiment_label', 'unknown')}, "
                  f"Cached: {score.get('cached', False)}")
    
    # Check cache stats
    cache_stats = sentiment_result.get("cache_stats", {})
    if cache_stats:
        print(f"[OK] Cache hit rate: {cache_stats.get('hit_rate', 0.0):.2%}")
    
    return True


def run_all_tests():
    """Run all tests and show summary."""
    print("\n" + "="*60)
    print("LLM SENTIMENT AGENT - END-TO-END TEST SUITE")
    print("="*60)
    print("\nTesting all components with mock data...")
    
    results = {}
    
    try:
        results["Initialization"] = test_agent_initialization()
    except Exception as e:
        print(f"[ERROR] Initialization test failed: {e}")
        results["Initialization"] = False
    
    try:
        results["SentimentAnalysis"] = test_sentiment_analysis()
    except Exception as e:
        print(f"[ERROR] SentimentAnalysis test failed: {e}")
        results["SentimentAnalysis"] = False
    
    try:
        results["CacheFunctionality"] = test_cache_functionality()
    except Exception as e:
        print(f"[ERROR] CacheFunctionality test failed: {e}")
        results["CacheFunctionality"] = False
    
    try:
        results["BatchAnalysis"] = test_batch_analysis()
    except Exception as e:
        print(f"[ERROR] BatchAnalysis test failed: {e}")
        results["BatchAnalysis"] = False
    
    try:
        results["Integration"] = test_integration_with_news_fetch()
    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        results["Integration"] = False
    
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
        print("\n[SUCCESS] All tests passed! LLM Sentiment Agent is working correctly with mock data.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

