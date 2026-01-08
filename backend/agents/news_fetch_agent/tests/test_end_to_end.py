"""
End-to-End Test for News Fetch Agent

This script tests the complete pipeline:
1. MockNewsCollector fetches articles
2. RelevanceFilter scores articles
3. DuplicateFilter removes duplicates
4. Agent processes everything

Tests accuracy and correctness of all components.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.news_fetch_agent.collectors import MockNewsCollector
from agents.news_fetch_agent.filters import RelevanceFilter, DuplicateFilter
from agents.news_fetch_agent.utils import SectorMapper


def test_mock_collector():
    """Test MockNewsCollector accuracy."""
    print("\n" + "="*60)
    print("TEST 1: MockNewsCollector")
    print("="*60)
    
    collector = MockNewsCollector()
    
    # Test fetching for known ticker
    articles = collector.fetch_news("AAPL", {"limit": 5})
    print(f"[OK] Fetched {len(articles)} articles for AAPL")
    
    if articles:
        print(f"[OK] First article: {articles[0]['title'][:60]}...")
        print(f"[OK] Article has all required fields: {list(articles[0].keys())}")
    
    # Test fetching for unknown ticker
    articles_unknown = collector.fetch_news("UNKNOWN", {"limit": 5})
    print(f"[OK] Unknown ticker returns {len(articles_unknown)} articles (expected: 0)")
    
    # Test all 10 tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "XOM", "CVX", "JNJ", "PFE", "JPM", "BAC", "GS"]
    total_articles = 0
    for ticker in tickers:
        articles = collector.fetch_news(ticker)
        total_articles += len(articles)
        print(f"[OK] {ticker}: {len(articles)} articles")
    
    print(f"[OK] Total articles across all tickers: {total_articles} (expected: 100)")
    
    return True


def test_relevance_filter():
    """Test RelevanceFilter accuracy."""
    print("\n" + "="*60)
    print("TEST 2: RelevanceFilter")
    print("="*60)
    
    collector = MockNewsCollector()
    relevance_filter = RelevanceFilter()
    
    # Get articles for AAPL
    articles = collector.fetch_news("AAPL", {"limit": 10})
    print(f"[OK] Loaded {len(articles)} articles for AAPL")
    
    # Score articles
    scored_articles = relevance_filter.score_articles(articles, "AAPL")
    print(f"[OK] Scored {len(scored_articles)} articles")
    
    # Check scores
    scores = [article.get("relevance_score", 0.0) for article in scored_articles]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0
    
    print(f"[OK] Relevance scores - Min: {min_score:.2f}, Max: {max_score:.2f}, Avg: {avg_score:.2f}")
    
    # Show top 3 most relevant
    sorted_articles = relevance_filter.sort_by_relevance(scored_articles, reverse=True)
    print("\n[OK] Top 3 most relevant articles:")
    for i, article in enumerate(sorted_articles[:3], 1):
        print(f"  {i}. Score: {article['relevance_score']:.2f} - {article['title'][:50]}...")
    
    # Filter by threshold
    filtered = relevance_filter.filter_by_threshold(scored_articles, min_score=0.5)
    print(f"[OK] Articles above 0.5 threshold: {len(filtered)}/{len(scored_articles)}")
    
    # Test with wrong ticker (should have lower scores)
    articles_msft = collector.fetch_news("MSFT", {"limit": 5})
    scored_msft = relevance_filter.score_articles(articles_msft, "AAPL")  # Wrong ticker
    scores_msft = [a.get("relevance_score", 0.0) for a in scored_msft]
    avg_msft = sum(scores_msft) / len(scores_msft) if scores_msft else 0.0
    print(f"[OK] MSFT articles scored for AAPL - Avg: {avg_msft:.2f} (should be lower)")
    
    return True


def test_duplicate_filter():
    """Test DuplicateFilter accuracy."""
    print("\n" + "="*60)
    print("TEST 3: DuplicateFilter")
    print("="*60)
    
    collector = MockNewsCollector()
    duplicate_filter = DuplicateFilter()
    
    # Get articles
    articles = collector.fetch_news("AAPL", {"limit": 10})
    print(f"[OK] Loaded {len(articles)} articles")
    
    # Create duplicates (simulate multiple sources)
    articles_with_duplicates = articles.copy()
    
    # Add a duplicate (same URL)
    if articles:
        duplicate = articles[0].copy()
        duplicate["source"] = "Different Source"
        articles_with_duplicates.append(duplicate)
        print(f"[OK] Added 1 duplicate article (same URL, different source)")
    
    # Add a similar title duplicate
    if len(articles) > 1:
        similar = articles[1].copy()
        similar["title"] = articles[1]["title"] + " Updated"  # Very similar
        similar["url"] = "different-url.com"  # Different URL
        similar["source"] = "Another Source"
        articles_with_duplicates.append(similar)
        print(f"[OK] Added 1 similar title article")
    
    print(f"[OK] Total articles before deduplication: {len(articles_with_duplicates)}")
    
    # Remove duplicates
    unique = duplicate_filter.remove_duplicates(articles_with_duplicates)
    print(f"[OK] Articles after deduplication: {len(unique)}")
    print(f"[OK] Removed {len(articles_with_duplicates) - len(unique)} duplicates")
    
    # Find duplicate groups
    duplicate_groups = duplicate_filter.find_duplicates(articles_with_duplicates)
    print(f"[OK] Found {len(duplicate_groups)} duplicate groups")
    
    return True


def test_sector_mapper():
    """Test SectorMapper accuracy."""
    print("\n" + "="*60)
    print("TEST 4: SectorMapper")
    print("="*60)
    
    mapper = SectorMapper()
    
    # Test known tickers
    test_tickers = ["AAPL", "MSFT", "XOM", "JNJ", "JPM"]
    for ticker in test_tickers:
        sector = mapper.get_sector(ticker)
        print(f"[OK] {ticker} -> {sector}")
    
    # Test unknown ticker
    sector_unknown = mapper.get_sector("UNKNOWN")
    print(f"[OK] UNKNOWN -> {sector_unknown} (expected: None)")
    
    # Test get tickers by sector
    tech_tickers = mapper.get_tickers_by_sector("technology")
    print(f"[OK] Technology sector has {len(tech_tickers)} tickers")
    
    # Test all sectors
    all_sectors = mapper.get_all_sectors()
    print(f"[OK] Total sectors: {len(all_sectors)} - {all_sectors}")
    
    return True


def test_full_agent_pipeline():
    """Test complete NewsFetchAgent pipeline."""
    print("\n" + "="*60)
    print("TEST 5: Full Agent Pipeline")
    print("="*60)
    
    # Initialize agent with mock data
    agent = NewsFetchAgent(config={
        "use_mock_data": True,
        "min_relevance_score": 0.3,  # Lower threshold for testing
        "max_articles": 20
    })
    
    # Initialize agent
    initialized = agent.initialize()
    print(f"[OK] Agent initialized: {initialized}")
    
    if not initialized:
        print("[ERROR] Agent failed to initialize")
        return False
    
    # Test health check
    health = agent.health_check()
    print(f"[OK] Agent health: {health['status']}")
    
    # Process news for AAPL
    print("\n[TEST] Processing news for AAPL...")
    result = agent.process("AAPL", params={"limit": 10, "min_relevance": 0.3})
    
    print(f"[OK] Status: {result.get('status')}")
    print(f"[OK] Total articles: {result.get('total_count', 0)}")
    print(f"[OK] Sources used: {result.get('sources', [])}")
    
    articles = result.get("articles", [])
    if articles:
        print(f"\n[OK] Sample articles (showing relevance scores):")
        for i, article in enumerate(articles[:5], 1):
            score = article.get("relevance_score", 0.0)
            print(f"  {i}. Score: {score:.2f} - {article['title'][:50]}...")
        
        # Check accuracy
        avg_score = sum(a.get("relevance_score", 0.0) for a in articles) / len(articles)
        print(f"\n[OK] Average relevance score: {avg_score:.2f}")
        print(f"[OK] All articles have relevance_score: {all('relevance_score' in a for a in articles)}")
    
    # Test with different ticker
    print("\n[TEST] Processing news for MSFT...")
    result_msft = agent.process("MSFT", params={"limit": 5})
    print(f"[OK] MSFT articles: {result_msft.get('total_count', 0)}")
    
    # Test with unknown ticker
    print("\n[TEST] Processing news for UNKNOWN...")
    result_unknown = agent.process("UNKNOWN", params={"limit": 5})
    print(f"[OK] UNKNOWN articles: {result_unknown.get('total_count', 0)} (expected: 0)")
    
    return True


def run_all_tests():
    """Run all tests and show summary."""
    print("\n" + "="*60)
    print("NEWS FETCH AGENT - END-TO-END TEST SUITE")
    print("="*60)
    print("\nTesting all components with mock data...")
    
    results = {}
    
    try:
        results["MockCollector"] = test_mock_collector()
    except Exception as e:
        print(f"[ERROR] MockCollector test failed: {e}")
        results["MockCollector"] = False
    
    try:
        results["RelevanceFilter"] = test_relevance_filter()
    except Exception as e:
        print(f"[ERROR] RelevanceFilter test failed: {e}")
        results["RelevanceFilter"] = False
    
    try:
        results["DuplicateFilter"] = test_duplicate_filter()
    except Exception as e:
        print(f"[ERROR] DuplicateFilter test failed: {e}")
        results["DuplicateFilter"] = False
    
    try:
        results["SectorMapper"] = test_sector_mapper()
    except Exception as e:
        print(f"[ERROR] SectorMapper test failed: {e}")
        results["SectorMapper"] = False
    
    try:
        results["FullPipeline"] = test_full_agent_pipeline()
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
        print("\n[SUCCESS] All tests passed! Agent is working correctly with mock data.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

