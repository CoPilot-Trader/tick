"""
Test script to verify API usage tracking for collectors.
This will help identify why Finnhub and NewsAPI counters stay constant.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path (go up two levels: scripts -> developer1 -> backend)
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.news_fetch_agent.collectors import FinnhubCollector, NewsAPICollector, AlphaVantageCollector

load_dotenv()

def test_collector_tracking(collector_class, collector_name, api_key_env_var):
    """Test API usage tracking for a collector."""
    api_key = os.getenv(api_key_env_var)
    if not api_key or not api_key.strip():
        print(f"\n{collector_name}: No API key found, skipping test")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing {collector_name} API Usage Tracking")
    print(f"{'='*60}")
    
    try:
        config = {"api_key": api_key.strip()}
        collector = collector_class(config=config)
        
        # Test 1: Initial state
        print("\n[Test 1] Initial state (before any calls):")
        usage1 = collector.get_api_usage_info()
        print(f"  Calls made: {usage1.get('calls_made', 'N/A')}")
        print(f"  Calls remaining: {usage1.get('calls_remaining', 'N/A')}")
        print(f"  Rate limit: {usage1.get('rate_limit', 'N/A')}")
        
        # Test 2: After first fetch
        print("\n[Test 2] After first fetch_news() call:")
        try:
            articles = collector.fetch_news("AAPL", {"limit": 5})
            print(f"  Fetched {len(articles)} articles")
        except Exception as e:
            print(f"  Fetch failed: {e}")
        
        usage2 = collector.get_api_usage_info()
        print(f"  Calls made: {usage2.get('calls_made', 'N/A')}")
        print(f"  Calls remaining: {usage2.get('calls_remaining', 'N/A')}")
        
        # Test 3: After second fetch (should increment)
        print("\n[Test 3] After second fetch_news() call:")
        time.sleep(1)  # Small delay
        try:
            articles = collector.fetch_news("MSFT", {"limit": 5})
            print(f"  Fetched {len(articles)} articles")
        except Exception as e:
            print(f"  Fetch failed: {e}")
        
        usage3 = collector.get_api_usage_info()
        print(f"  Calls made: {usage3.get('calls_made', 'N/A')}")
        print(f"  Calls remaining: {usage3.get('calls_remaining', 'N/A')}")
        
        # Test 4: Check internal state
        print("\n[Test 4] Internal state inspection:")
        if hasattr(collector, '_calls_made'):
            print(f"  _calls_made: {collector._calls_made}")
        if hasattr(collector, '_last_reset_time'):
            print(f"  _last_reset_time: {collector._last_reset_time}")
        if hasattr(collector, '_last_reset_date'):
            print(f"  _last_reset_date: {collector._last_reset_date}")
        
        # Verify counter increased
        if usage2.get('calls_made', 0) < usage3.get('calls_made', 0):
            print(f"\n[PASS] Counter increased from {usage2.get('calls_made')} to {usage3.get('calls_made')}")
        else:
            print(f"\n[FAIL] Counter did not increase! ({usage2.get('calls_made')} -> {usage3.get('calls_made')})")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing API Usage Tracking for News Collectors")
    print("=" * 60)
    
    # Test each collector
    test_collector_tracking(FinnhubCollector, "Finnhub", "FINNHUB_API_KEY")
    test_collector_tracking(NewsAPICollector, "NewsAPI", "NEWSAPI_KEY")
    test_collector_tracking(AlphaVantageCollector, "Alpha Vantage", "ALPHA_VANTAGE_API_KEY")
    
    print("\n" + "="*60)
    print("Testing complete!")

