"""Test to check if collectors are initialized correctly."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path (go up two levels: scripts -> developer1 -> backend)
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from agents.news_fetch_agent.agent import NewsFetchAgent

load_dotenv()

# Check API keys
finnhub = os.getenv('FINNHUB_API_KEY')
newsapi = os.getenv('NEWSAPI_KEY')
alpha = os.getenv('ALPHA_VANTAGE_API_KEY')

print("API Keys Status:")
print(f"  Finnhub: {'[SET]' if (finnhub and finnhub.strip()) else '[NOT SET]'}")
print(f"  NewsAPI: {'[SET]' if (newsapi and newsapi.strip()) else '[NOT SET]'}")
print(f"  Alpha Vantage: {'[SET]' if (alpha and alpha.strip()) else '[NOT SET]'}")

# Initialize agent
config = {
    'use_mock_data': False,
    'finnhub_api_key': finnhub.strip() if finnhub and finnhub.strip() else None,
    'newsapi_key': newsapi.strip() if newsapi and newsapi.strip() else None,
    'alpha_vantage_api_key': alpha.strip() if alpha and alpha.strip() else None,
}

agent = NewsFetchAgent(config=config)
agent.initialize()

print(f"\nInitialized Collectors:")
for collector in agent.collectors:
    print(f"  - {collector.get_source_name()}")
    usage = collector.get_api_usage_info()
    print(f"    Calls Made: {usage.get('calls_made', 'N/A')}")
    print(f"    Calls Remaining: {usage.get('calls_remaining', 'N/A')}")
    print(f"    Is Mock: {usage.get('is_mock', 'N/A')}")

