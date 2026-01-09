"""
Verification script to test API usage tracking through the actual pipeline endpoint.
This simulates multiple frontend requests to verify counters decrease correctly.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_pipeline_request(symbol="AAPL", min_relevance=0.3, max_articles=10, time_horizon="1d"):
    """Make a request to the pipeline visualizer endpoint."""
    url = f"{BASE_URL}/api/v1/news-pipeline/visualize"
    payload = {
        "symbol": symbol,
        "min_relevance": min_relevance,
        "max_articles": max_articles,
        "time_horizon": time_horizon
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error making request: {e}")
        return None

def extract_api_usage(data):
    """Extract API usage info from the response."""
    if not data or "steps" not in data:
        return None
    
    step1 = None
    for step in data["steps"]:
        if step.get("agent") == "news_fetch_agent":
            step1 = step
            break
    
    if not step1 or "details" not in step1:
        return None
    
    api_usage = step1["details"].get("api_usage", [])
    return api_usage

def format_usage_info(usage_info):
    """Format API usage info for display."""
    if not usage_info:
        return "No API usage info"
    
    formatted = []
    for info in usage_info:
        source = info.get("source", "Unknown")
        is_mock = info.get("is_mock", False)
        calls_made = info.get("calls_made", "N/A")
        calls_remaining = info.get("calls_remaining", "N/A")
        rate_limit = info.get("rate_limit", "N/A")
        
        if is_mock:
            formatted.append(f"{source}: Mock (Unlimited)")
        else:
            formatted.append(f"{source}: {calls_remaining} remaining (made: {calls_made}, limit: {rate_limit})")
    
    return " | ".join(formatted)

def main():
    print("=" * 80)
    print("API Usage Tracking Verification")
    print("=" * 80)
    print("\nThis script will make 3 consecutive requests to verify that")
    print("API usage counters decrease correctly for all three APIs.\n")
    
    # Test with different symbols to ensure we're making real API calls
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    previous_usage = None
    
    for i, symbol in enumerate(test_symbols, 1):
        print(f"\n{'='*80}")
        print(f"Request #{i}: Fetching news for {symbol}")
        print(f"{'='*80}")
        
        start_time = time.time()
        result = test_pipeline_request(symbol=symbol, min_relevance=0.3, max_articles=10)
        elapsed = time.time() - start_time
        
        if not result:
            print(f"[ERROR] Request failed!")
            continue
        
        # Check status
        status = result.get("status", "unknown")
        print(f"Status: {status}")
        print(f"Response time: {elapsed:.2f}s")
        
        # Extract API usage
        api_usage = extract_api_usage(result)
        current_usage = format_usage_info(api_usage)
        print(f"API Usage: {current_usage}")
        
        # Compare with previous request
        if previous_usage and api_usage:
            print(f"\n[Comparison] Comparison with previous request:")
            for current_info in api_usage:
                source = current_info.get("source")
                current_remaining = current_info.get("calls_remaining")
                is_mock = current_info.get("is_mock", False)
                
                if is_mock:
                    continue
                
                # Find corresponding info from previous request
                prev_info = None
                for p in previous_usage:
                    if p.get("source") == source:
                        prev_info = p
                        break
                
                if prev_info:
                    prev_remaining = prev_info.get("calls_remaining")
                    if prev_remaining is not None and current_remaining is not None:
                        if current_remaining < prev_remaining:
                            print(f"  [PASS] {source}: {prev_remaining} -> {current_remaining} (decreased)")
                        elif current_remaining == prev_remaining:
                            print(f"  [WARN] {source}: {prev_remaining} -> {current_remaining} (unchanged)")
                        else:
                            print(f"  [INFO] {source}: {prev_remaining} -> {current_remaining} (increased - possible reset)")
        
        previous_usage = api_usage
        
        # Small delay between requests
        if i < len(test_symbols):
            print(f"\nWaiting 2 seconds before next request...")
            time.sleep(2)
    
    print(f"\n{'='*80}")
    print("Verification Complete!")
    print(f"{'='*80}")
    print("\nExpected behavior:")
    print("  - All three APIs (Finnhub, NewsAPI, Alpha Vantage) should show")
    print("    decreasing 'calls_remaining' values with each request")
    print("  - If counters stay constant, there may still be an issue")
    print("  - If counters reset, the time window may have passed (normal)")

if __name__ == "__main__":
    main()

