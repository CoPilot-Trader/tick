"""
Test script to verify API key detection and collector initialization.

Run this to check if your API keys are being detected correctly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path (go up two levels: scripts -> developer1 -> backend)
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Load environment variables
load_dotenv()

print("=" * 60)
print("API Key Detection Test")
print("=" * 60)

# Check environment variables
finnhub_key = os.getenv("FINNHUB_API_KEY")
newsapi_key = os.getenv("NEWSAPI_KEY")
alphavantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

print("\n1. Environment Variables:")
print(f"   FINNHUB_API_KEY: {'[SET]' if finnhub_key and finnhub_key.strip() else '[NOT SET or EMPTY]'}")
if finnhub_key and finnhub_key.strip():
    print(f"      Value: {finnhub_key[:10]}...{finnhub_key[-4:] if len(finnhub_key) > 14 else '***'}")

print(f"   NEWSAPI_KEY: {'[SET]' if newsapi_key and newsapi_key.strip() else '[NOT SET or EMPTY]'}")
if newsapi_key and newsapi_key.strip():
    print(f"      Value: {newsapi_key[:10]}...{newsapi_key[-4:] if len(newsapi_key) > 14 else '***'}")

print(f"   ALPHA_VANTAGE_API_KEY: {'[SET]' if alphavantage_key and alphavantage_key.strip() else '[NOT SET or EMPTY]'}")
if alphavantage_key and alphavantage_key.strip():
    print(f"      Value: {alphavantage_key[:10]}...{alphavantage_key[-4:] if len(alphavantage_key) > 14 else '***'}")

# Check .env file
env_file = backend_path / ".env"
print(f"\n2. .env File:")
if env_file.exists():
    print(f"   [FOUND]: {env_file}")
    with open(env_file, 'r') as f:
        content = f.read()
        has_finnhub = "FINNHUB_API_KEY" in content
        has_newsapi = "NEWSAPI_KEY" in content
        has_alphavantage = "ALPHA_VANTAGE_API_KEY" in content
        print(f"   FINNHUB_API_KEY in file: {'[YES]' if has_finnhub else '[NO]'}")
        print(f"   NEWSAPI_KEY in file: {'[YES]' if has_newsapi else '[NO]'}")
        print(f"   ALPHA_VANTAGE_API_KEY in file: {'[YES]' if has_alphavantage else '[NO]'}")
else:
    print(f"   [NOT FOUND]: {env_file}")
    print(f"   Create a .env file in: {backend_path}")

# Test agent initialization
print(f"\n3. Agent Initialization Test:")
try:
    from agents.news_fetch_agent.agent import NewsFetchAgent
    
    has_finnhub = finnhub_key and finnhub_key.strip()
    has_newsapi = newsapi_key and newsapi_key.strip()
    has_alphavantage = alphavantage_key and alphavantage_key.strip()
    
    use_mock_data = not (has_finnhub or has_newsapi or has_alphavantage)
    
    news_config = {
        "use_mock_data": use_mock_data,
    }
    if has_finnhub:
        news_config["finnhub_api_key"] = finnhub_key.strip()
    if has_newsapi:
        news_config["newsapi_key"] = newsapi_key.strip()
    if has_alphavantage:
        news_config["alpha_vantage_api_key"] = alphavantage_key.strip()
    
    agent = NewsFetchAgent(config=news_config)
    agent.initialize()
    
    print(f"   use_mock_data: {agent.use_mock_data}")
    print(f"   Collectors initialized: {len(agent.collectors)}")
    for collector in agent.collectors:
        source_name = collector.get_source_name()
        usage_info = collector.get_api_usage_info()
        is_mock = usage_info.get("is_mock", False)
        print(f"      - {source_name}: {'[Mock]' if is_mock else '[Real API]'}")
    
    print(f"\n   Expected data_source: {'mock' if use_mock_data else 'api'}")
    
except Exception as e:
    print(f"   [ERROR]: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("To use real APIs:")
print("1. Create a .env file in tick/backend/")
print("2. Add your API keys:")
print("   FINNHUB_API_KEY=your_key_here")
print("   NEWSAPI_KEY=your_key_here")
print("   ALPHA_VANTAGE_API_KEY=your_key_here")
print("3. Restart the backend server")
print("=" * 60)

