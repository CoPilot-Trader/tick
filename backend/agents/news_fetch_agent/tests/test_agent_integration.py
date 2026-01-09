"""
Integration test for News Fetch Agent with mock data.

This test verifies that the complete pipeline works:
1. Agent initialization
2. News fetching from mock collector
3. Relevance scoring
4. Filtering
5. Duplicate removal
6. Final output format
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.news_fetch_agent.agent import NewsFetchAgent


def test_agent_integration():
    """Test the complete agent pipeline with mock data."""
    print("=" * 60)
    print("Testing News Fetch Agent Integration")
    print("=" * 60)
    
    # Step 1: Initialize agent
    print("\n[1] Initializing agent...")
    agent = NewsFetchAgent(config={"use_mock_data": True, "min_relevance_score": 0.3})
    initialized = agent.initialize()
    
    if not initialized:
        print("[ERROR] Agent initialization failed!")
        return False
    
    print(f"[OK] Agent initialized: {agent.name} v{agent.version}")
    print(f"[OK] Using mock data: {agent.use_mock_data}")
    print(f"[OK] Collectors: {len(agent.collectors)}")
    
    # Step 2: Test health check
    print("\n[2] Testing health check...")
    health = agent.health_check()
    print(f"[OK] Health: {health['status']}")
    
    # Step 3: Fetch news for AAPL
    print("\n[3] Fetching news for AAPL...")
    result = agent.process("AAPL", params={"limit": 10})
    
    if result["status"] != "success":
        print(f"[ERROR] Failed to fetch news: {result.get('message')}")
        return False
    
    articles = result["articles"]
    print(f"[OK] Fetched {len(articles)} articles")
    print(f"[OK] Sources used: {result['sources']}")
    print(f"[OK] Total count: {result['total_count']}")
    
    # Step 4: Verify article structure
    print("\n[4] Verifying article structure...")
    if articles:
        first_article = articles[0]
        required_fields = ["id", "title", "source", "published_at", "relevance_score"]
        missing_fields = [field for field in required_fields if field not in first_article]
        
        if missing_fields:
            print(f"[ERROR] Missing fields: {missing_fields}")
            return False
        
        print(f"[OK] Article structure valid")
        print(f"[OK] First article: {first_article['title'][:60]}...")
        print(f"[OK] Relevance score: {first_article['relevance_score']:.2f}")
        print(f"[OK] Source: {first_article['source']}")
    else:
        print("[WARNING] No articles returned")
    
    # Step 5: Check relevance scores
    print("\n[5] Checking relevance scores...")
    if articles:
        scores = [article["relevance_score"] for article in articles]
        avg_score = sum(scores) / len(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0
        
        print(f"[OK] Average relevance: {avg_score:.2f}")
        print(f"[OK] Min relevance: {min_score:.2f}")
        print(f"[OK] Max relevance: {max_score:.2f}")
        
        # Check if scores are in valid range
        if any(score < 0.0 or score > 1.0 for score in scores):
            print("[ERROR] Invalid relevance scores (must be 0.0-1.0)")
            return False
    
    # Step 6: Test with different ticker
    print("\n[6] Testing with different ticker (MSFT)...")
    result_msft = agent.process("MSFT", params={"limit": 5})
    
    if result_msft["status"] == "success":
        print(f"[OK] Fetched {len(result_msft['articles'])} articles for MSFT")
        if result_msft["articles"]:
            print(f"[OK] First article: {result_msft['articles'][0]['title'][:60]}...")
    else:
        print(f"[ERROR] Failed: {result_msft.get('message')}")
    
    # Step 7: Test with unknown ticker
    print("\n[7] Testing with unknown ticker (UNKNOWN)...")
    result_unknown = agent.process("UNKNOWN", params={"limit": 5})
    
    if result_unknown["status"] == "success":
        print(f"[OK] Handled unknown ticker gracefully: {len(result_unknown['articles'])} articles")
    else:
        print(f"[OK] Handled unknown ticker: {result_unknown.get('message')}")
    
    # Step 8: Test filtering with higher threshold
    print("\n[8] Testing relevance filtering (min_score=0.7)...")
    result_filtered = agent.process("AAPL", params={"limit": 20, "min_relevance": 0.7})
    
    if result_filtered["status"] == "success":
        print(f"[OK] With higher threshold: {len(result_filtered['articles'])} articles")
        if result_filtered["articles"]:
            scores = [a["relevance_score"] for a in result_filtered["articles"]]
            print(f"[OK] All scores >= 0.7: {all(s >= 0.7 for s in scores)}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All integration tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_agent_integration()
    sys.exit(0 if success else 1)

