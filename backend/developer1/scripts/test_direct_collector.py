"""Test collectors directly to see if calls are being made."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Add backend to path (go up two levels: scripts -> developer1 -> backend)
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.news_fetch_agent.agent import NewsFetchAgent

load_dotenv()

config = {
    'use_mock_data': False,
    'finnhub_api_key': os.getenv('FINNHUB_API_KEY', '').strip(),
    'newsapi_key': os.getenv('NEWSAPI_KEY', '').strip(),
    'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY', '').strip(),
}

agent = NewsFetchAgent(config=config)
agent.initialize()

# Test making calls
print("=" * 60)
print("Testing Direct Collector Calls")
print("=" * 60)

to_date = datetime.now(timezone.utc)
from_date = to_date - timedelta(days=3)

params = {
    'from_date': from_date,
    'to_date': to_date,
    'limit': 5
}

for i in range(1, 4):
    print(f"\n--- Call #{i} ---")
    for collector in agent.collectors:
        name = collector.get_source_name()
        print(f"\n{name}:")
        try:
            # Get usage before
            usage_before = collector.get_api_usage_info()
            print(f"  Before: Calls Made={usage_before.get('calls_made')}, Remaining={usage_before.get('calls_remaining')}")
            
            # Make call
            articles = collector.fetch_news("AAPL", params)
            print(f"  Fetched {len(articles)} articles")
            
            # Get usage after
            usage_after = collector.get_api_usage_info()
            print(f"  After: Calls Made={usage_after.get('calls_made')}, Remaining={usage_after.get('calls_remaining')}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            usage_after = collector.get_api_usage_info()
            print(f"  After (despite error): Calls Made={usage_after.get('calls_made')}, Remaining={usage_after.get('calls_remaining')}")
    
    if i < 3:
        import time
        time.sleep(1)

