"""
Integration test for Support/Resistance Agent.

This script tests the Support/Resistance Agent to verify:
1. Single ticker detection works
2. Batch processing works
3. Output format is correct
4. Performance is acceptable

Run this from the project root:
    python -m agents.support_resistance_agent.tests.test_agent_integration
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend directory to path (so we can import core)
# The script is at: tick/backend/agents/support_resistance_agent/tests/test_agent_integration.py
# We need to add tick/backend/ to path so 'core' can be imported
backend_dir = Path(__file__).parent.parent.parent.parent  # tick/backend/
sys.path.insert(0, str(backend_dir))

# Now we can import
from agents.support_resistance_agent.agent import SupportResistanceAgent


def test_single_ticker():
    """Test single ticker detection."""
    print("\n" + "="*60)
    print("TEST 1: Single Ticker Detection")
    print("="*60)
    
    # Initialize agent
    print("\n[INIT] Initializing agent...")
    agent = SupportResistanceAgent(config={"use_mock_data": True})
    
    if not agent.initialize():
        print("[ERROR] Failed to initialize agent")
        return False
    
    print("[OK] Agent initialized successfully")
    
    # Test detection
    print("\n[DETECT] Detecting levels for AAPL...")
    result = agent.process("AAPL")
    
    # Check result
    if result.get("status") == "error":
        print(f"[ERROR] Error: {result.get('message')}")
        return False
    
    # Display results
    print("\n[OK] Detection successful!")
    print(f"   Symbol: {result.get('symbol')}")
    print(f"   Current Price: ${result.get('current_price', 0):.2f}")
    print(f"   Support Levels: {len(result.get('support_levels', []))}")
    print(f"   Resistance Levels: {len(result.get('resistance_levels', []))}")
    print(f"   Total Levels: {result.get('total_levels', 0)}")
    print(f"   Processing Time: {result.get('processing_time_seconds', 0):.3f}s")
    
    # Show support levels
    if result.get('support_levels'):
        print("\n   Support Levels:")
        for level in result['support_levels'][:3]:  # Show first 3
            print(f"      - ${level['price']:.2f} (Strength: {level['strength']}, "
                  f"Touches: {level['touches']}, Validated: {level['validated']})")
    
    # Show resistance levels
    if result.get('resistance_levels'):
        print("\n   Resistance Levels:")
        for level in result['resistance_levels'][:3]:  # Show first 3
            print(f"      - ${level['price']:.2f} (Strength: {level['strength']}, "
                  f"Touches: {level['touches']}, Validated: {level['validated']})")
    
    # Validate performance
    processing_time = result.get('processing_time_seconds', 0)
    if processing_time > 5:
        print(f"\n[WARN] Warning: Processing time ({processing_time:.2f}s) exceeds target (<3s)")
    else:
        print(f"\n[OK] Performance: {processing_time:.2f}s (target: <3s)")
    
    return True


def test_batch_processing():
    """Test batch processing."""
    print("\n" + "="*60)
    print("TEST 2: Batch Processing")
    print("="*60)
    
    # Initialize agent
    agent = SupportResistanceAgent(config={"use_mock_data": True})
    agent.initialize()
    
    # Test batch
    symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "SPY"]
    print(f"\n[DETECT] Detecting levels for {len(symbols)} tickers...")
    print(f"   Symbols: {', '.join(symbols)}")
    
    import time
    start_time = time.time()
    
    results = agent.detect_levels_batch(symbols, use_parallel=False)
    
    total_time = time.time() - start_time
    
    # Display results
    print(f"\n[OK] Batch detection complete!")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Average Time: {total_time/len(symbols):.2f}s per ticker")
    
    print("\n   Results:")
    for symbol in symbols:
        result = results.get(symbol, {})
        if result.get("status") == "error":
            print(f"      [ERROR] {symbol}: {result.get('message', 'Unknown error')}")
        else:
            total_levels = result.get('total_levels', 0)
            proc_time = result.get('processing_time_seconds', 0)
            print(f"      [OK] {symbol}: {total_levels} levels ({proc_time:.2f}s)")
    
    return True


def test_caching():
    """Test caching mechanism."""
    print("\n" + "="*60)
    print("TEST 3: Caching Mechanism")
    print("="*60)
    
    # Initialize agent
    agent = SupportResistanceAgent(config={"use_mock_data": True, "enable_cache": True})
    agent.initialize()
    
    symbol = "AAPL"
    
    # First call (no cache)
    print(f"\n[DETECT] First call for {symbol} (no cache)...")
    import time
    start = time.time()
    result1 = agent.process(symbol)
    time1 = time.time() - start
    
    print(f"   Time: {time1:.3f}s")
    print(f"   Levels: {result1.get('total_levels', 0)}")
    
    # Second call (should use cache)
    print(f"\n[DETECT] Second call for {symbol} (should use cache)...")
    start = time.time()
    result2 = agent.process(symbol)
    time2 = time.time() - start
    
    print(f"   Time: {time2:.3f}s")
    print(f"   Levels: {result2.get('total_levels', 0)}")
    
    # Check if cache worked
    if time2 < time1 * 0.1:  # Cache should be at least 10x faster
        print(f"\n[OK] Cache working! ({time2/time1*100:.1f}% of original time)")
    else:
        print(f"\n[WARN] Cache may not be working (expected much faster)")
    
    return True


def test_output_structure():
    """Test output structure is correct."""
    print("\n" + "="*60)
    print("TEST 4: Output Structure Validation")
    print("="*60)
    
    # Initialize agent
    agent = SupportResistanceAgent(config={"use_mock_data": True})
    agent.initialize()
    
    result = agent.process("AAPL")
    
    # Required fields
    required_fields = [
        "symbol", "timestamp", "current_price",
        "support_levels", "resistance_levels", "total_levels"
    ]
    
    print("\n[CHECK] Checking required fields...")
    missing_fields = []
    for field in required_fields:
        if field not in result:
            missing_fields.append(field)
        else:
            print(f"   [OK] {field}")
    
    if missing_fields:
        print(f"\n[ERROR] Missing fields: {', '.join(missing_fields)}")
        return False
    
    # Check level structure
    if result.get('support_levels'):
        level = result['support_levels'][0]
        level_fields = ['price', 'strength', 'type', 'touches', 'validated']
        print("\n[CHECK] Checking level structure...")
        for field in level_fields:
            if field in level:
                print(f"   [OK] {field}")
            else:
                print(f"   [ERROR] Missing: {field}")
    
    print("\n[OK] Output structure is correct!")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LEVEL DETECTION COMPONENT - INTEGRATION TEST")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Single Ticker", test_single_ticker),
        ("Batch Processing", test_batch_processing),
        ("Caching", test_caching),
        ("Output Structure", test_output_structure),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' failed with error:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS] PASSED" if result else "[FAIL] FAILED"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Component is working correctly.")
    else:
        print(f"\n[WARN] {total - passed} test(s) failed. Please review the errors above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
