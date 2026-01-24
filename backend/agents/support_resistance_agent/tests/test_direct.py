"""
Direct test for Support/Resistance Agent (bypassing API).

This script tests the agent directly to diagnose issues.
Run this from the project root:
    python -m agents.support_resistance_agent.tests.test_direct
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent  # tick/backend/
sys.path.insert(0, str(backend_dir))

from agents.support_resistance_agent.agent import SupportResistanceAgent
import json

# Initialize agent
agent = SupportResistanceAgent({'use_mock_data': True})
agent.initialize()

# Test with min_strength=50
print("Testing with min_strength=50...")
result = agent.process('AAPL', {'min_strength': 50, 'max_levels': 10})

print(f"Support levels: {len(result.get('support_levels', []))}")
print(f"Resistance levels: {len(result.get('resistance_levels', []))}")

# Try JSON serialization
try:
    json_str = json.dumps(result, default=str, indent=2)
    print("JSON serialization: SUCCESS")
    print(f"JSON length: {len(json_str)} characters")
except Exception as e:
    print(f"JSON serialization ERROR: {e}")
    import traceback
    traceback.print_exc()
