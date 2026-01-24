"""
Diagnostic test script to check if yfinance is working.

Run this to diagnose why real data might not be loading.
Run from project root:
    python -m agents.support_resistance_agent.tests.test_yfinance_diagnostic
"""

import sys
from datetime import datetime, timezone, timedelta

print("=" * 60)
print("yfinance Diagnostic Test")
print("=" * 60)

# Test 1: Check if yfinance is installed
print("\n1. Checking if yfinance is installed...")
try:
    import yfinance as yf
    print(f"   [OK] yfinance is installed (version: {yf.__version__})")
except ImportError as e:
    print(f"   [ERROR] yfinance is NOT installed: {e}")
    print("   Install with: pip install yfinance")
    sys.exit(1)

# Test 2: Try to fetch data for AAPL
print("\n2. Testing data fetch for AAPL...")
try:
    ticker = yf.Ticker("AAPL")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    print(f"   Fetching data from {start_date.date()} to {end_date.date()}...")
    df = ticker.history(
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=True,
        prepost=False
    )
    
    if df.empty:
        print("   [ERROR] yfinance returned empty DataFrame")
        print("   This might be a network issue or symbol problem")
    else:
        print(f"   [OK] Successfully fetched {len(df)} data points")
        print(f"   Date range: {df.index.min()} to {df.index.max()}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Sample data:")
        print(df.head(3))
        
except Exception as e:
    print(f"   [ERROR] Error fetching data: {e}")
    import traceback
    print("\n   Full error traceback:")
    print(traceback.format_exc())

# Test 3: Check network connectivity
print("\n3. Checking network connectivity...")
try:
    import requests
    response = requests.get("https://finance.yahoo.com", timeout=5)
    if response.status_code == 200:
        print("   [OK] Can reach Yahoo Finance website")
    else:
        print(f"   [WARNING] Yahoo Finance returned status code: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Cannot reach Yahoo Finance: {e}")
    print("   This might be a network/firewall issue")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)
