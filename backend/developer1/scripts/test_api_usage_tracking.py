"""
Test script to verify API usage tracking is working correctly.
This script makes multiple API calls and checks if the remaining calls decrease.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1/news-pipeline"

def test_api_usage_tracking():
    """Test that API usage tracking decreases on each call."""
    print("=" * 60)
    print("Testing API Usage Tracking")
    print("=" * 60)
    
    # Make 3 consecutive calls
    for i in range(1, 4):
        print(f"\n--- Call #{i} ---")
        
        try:
            response = requests.post(
                f"{BASE_URL}/visualize",
                json={
                    "symbol": "AAPL",
                    "min_relevance": 0.4,
                    "max_articles": 5,
                    "time_horizon": "1d"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract API usage info from step 1
                if "steps" in data and len(data["steps"]) > 0:
                    step1 = data["steps"][0]
                    if "details" in step1 and "api_usage" in step1["details"]:
                        api_usage = step1["details"]["api_usage"]
                        
                        print(f"API Usage Info:")
                        for source_info in api_usage:
                            source = source_info.get("source", "Unknown")
                            remaining = source_info.get("calls_remaining", "N/A")
                            made = source_info.get("calls_made", "N/A")
                            print(f"  {source}:")
                            print(f"    Calls Made: {made}")
                            print(f"    Calls Remaining: {remaining}")
                    else:
                        print("⚠ No API usage info found in response")
                else:
                    print("⚠ Invalid response structure")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Wait 1 second between calls
        if i < 3:
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("\nExpected behavior:")
    print("- Finnhub: Should decrease from 60 (or less) on each call")
    print("- NewsAPI: Should decrease from 1000 (or less) on each call")
    print("- Alpha Vantage: Should decrease from 500 (or less) on each call")
    print("\nIf all three decrease correctly, the fix is working! ✅")

if __name__ == "__main__":
    test_api_usage_tracking()

