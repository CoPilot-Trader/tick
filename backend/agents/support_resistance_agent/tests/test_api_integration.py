"""
Integration test for Support/Resistance Agent API endpoints.

This script tests all API endpoints to ensure they work correctly.
Run this while the FastAPI server is running.

Usage:
    python -m agents.support_resistance_agent.tests.test_api_integration
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint and return the response."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"\n{method} {endpoint}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")  # Print first 500 chars
            return True, result
        else:
            print(f"Error: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to server at {BASE_URL}")
        print("Make sure the FastAPI server is running: uvicorn api.main:app --reload")
        return False, None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def main():
    """Run all API endpoint tests."""
    print_section("Support/Resistance Agent API Endpoint Tests")
    print(f"Testing endpoints at: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Health Check
    print_section("Test 1: Health Check")
    success, response = test_endpoint("GET", "/api/v1/levels/health")
    results.append(("Health Check", success))
    
    if not success:
        print("\n[WARNING] Server is not running or not accessible.")
        print("Please start the server with: cd tick/backend && uvicorn api.main:app --reload")
        return
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test 2: Get Levels for Single Symbol (GET)
    print_section("Test 2: Get Levels (GET) - AAPL")
    success, response = test_endpoint(
        "GET", 
        "/api/v1/levels/AAPL",
        params={"min_strength": 50, "max_levels": 5}
    )
    results.append(("Get Levels (GET)", success))
    
    # Test 3: Detect Levels (POST)
    print_section("Test 3: Detect Levels (POST) - TSLA")
    success, response = test_endpoint(
        "POST",
        "/api/v1/levels/detect",
        data={
            "symbol": "TSLA",
            "min_strength": 50,
            "max_levels": 5
        }
    )
    results.append(("Detect Levels (POST)", success))
    
    # Test 4: Get Nearest Levels
    print_section("Test 4: Get Nearest Levels - MSFT")
    success, response = test_endpoint(
        "GET",
        "/api/v1/levels/MSFT/nearest",
        params={"min_strength": 50}
    )
    results.append(("Get Nearest Levels", success))
    
    # Test 5: Batch Detection
    print_section("Test 5: Batch Detection - Multiple Symbols")
    success, response = test_endpoint(
        "POST",
        "/api/v1/levels/batch",
        data={
            "symbols": ["AAPL", "TSLA", "GOOGL"],
            "min_strength": 50,
            "max_levels": 3,
            "use_parallel": False
        }
    )
    results.append(("Batch Detection", success))
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
