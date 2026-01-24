"""
Unit Tests for Support/Resistance Agent

Tests for:
- Agent initialization
- Level detection process
- Batch processing
- Caching
- Error handling

Why unit tests?
- Verify agent orchestrates components correctly
- Test integration between components
- Ensure error handling works
- Validate output format
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from ..agent import SupportResistanceAgent
from ..interfaces import SupportResistanceResponse, PriceLevel


class TestSupportResistanceAgent:
    """
    Test suite for SupportResistanceAgent.
    
    Tests:
    - Initialization
    - Level detection
    - Batch processing
    - Caching
    - Error handling
    """
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        config = {"use_mock_data": True}
        agent = SupportResistanceAgent(config=config)
        
        assert agent.name == "support_resistance_agent", "Should have correct name"
        assert agent.version == "1.0.0", "Should have version"
        assert not agent.initialized, "Should not be initialized before initialize()"
        
        # Initialize
        result = agent.initialize()
        
        assert result is True, "Initialization should succeed"
        assert agent.initialized is True, "Should be initialized after initialize()"
        assert agent.data_loader is not None, "Data loader should be initialized"
        assert agent.extrema_detector is not None, "Extrema detector should be initialized"
        assert agent.clusterer is not None, "Clusterer should be initialized"
        assert agent.validator is not None, "Validator should be initialized"
        assert agent.strength_calculator is not None, "Strength calculator should be initialized"
    
    def test_process_single_ticker(self):
        """Test processing a single ticker."""
        agent = SupportResistanceAgent(config={"use_mock_data": True})
        agent.initialize()
        
        result = agent.process("AAPL")
        
        assert result is not None, "Should return a result"
        assert result.get('symbol') == "AAPL", "Should have correct symbol"
        assert 'support_levels' in result, "Should have support_levels"
        assert 'resistance_levels' in result, "Should have resistance_levels"
        assert 'total_levels' in result, "Should have total_levels"
        assert 'processing_time_seconds' in result, "Should have processing time"
    
    def test_process_with_params(self):
        """Test processing with custom parameters."""
        agent = SupportResistanceAgent(config={"use_mock_data": True})
        agent.initialize()
        
        result = agent.process(
            "AAPL",
            params={
                "min_strength": 60,
                "max_levels": 3
            }
        )
        
        assert result is not None, "Should return a result"
        # Verify levels meet criteria
        if result.get('support_levels'):
            assert all(l['strength'] >= 60 for l in result['support_levels']), \
                "All support levels should have strength >= 60"
            assert len(result['support_levels']) <= 3, \
                "Should have max 3 support levels"
    
    def test_detect_levels_batch(self):
        """Test batch level detection."""
        agent = SupportResistanceAgent(config={"use_mock_data": True})
        agent.initialize()
        
        symbols = ["AAPL", "TSLA"]
        results = agent.detect_levels_batch(symbols, use_parallel=False)
        
        assert len(results) == len(symbols), "Should process all symbols"
        assert all(s in results for s in symbols), "Should have results for all symbols"
        assert all('total_levels' in results[s] for s in symbols), \
            "All results should have total_levels"
    
    def test_caching(self):
        """Test result caching."""
        agent = SupportResistanceAgent(config={"use_mock_data": True, "enable_cache": True})
        agent.initialize()
        
        # First call
        result1 = agent.process("AAPL")
        
        # Second call (should use cache)
        result2 = agent.process("AAPL")
        
        # Results should be the same
        assert result1['total_levels'] == result2['total_levels'], \
            "Cached result should match original"
    
    def test_clear_cache(self):
        """Test cache clearing."""
        agent = SupportResistanceAgent(config={"use_mock_data": True, "enable_cache": True})
        agent.initialize()
        
        # Process and cache
        agent.process("AAPL")
        assert len(agent._cache) > 0, "Cache should have entries"
        
        # Clear cache
        agent.clear_cache("AAPL")
        assert len(agent._cache) == 0, "Cache should be cleared"
    
    def test_health_check(self):
        """Test health check."""
        agent = SupportResistanceAgent(config={"use_mock_data": True})
        
        # Before initialization
        health = agent.health_check()
        assert health['status'] == "not_initialized", "Should show not initialized"
        
        # After initialization
        agent.initialize()
        health = agent.health_check()
        assert health['status'] == "healthy", "Should show healthy"
        assert 'cache_size' in health, "Should show cache size"
        assert 'components_initialized' in health, "Should show component status"
    
    def test_error_handling_no_data(self):
        """Test error handling when no data is available."""
        agent = SupportResistanceAgent(config={"use_mock_data": True})
        agent.initialize()
        
        # Try with invalid symbol (should be handled gracefully)
        result = agent.process("INVALID_SYMBOL")
        
        # Should return error status, not crash
        assert result is not None, "Should return a result (even if error)"
        assert result.get('status') == 'error' or 'message' in result, \
            "Should indicate error status"
    
    def test_detect_levels_batch_parallel(self):
        """Test batch processing with parallel execution."""
        agent = SupportResistanceAgent(config={"use_mock_data": True})
        agent.initialize()
        
        symbols = ["AAPL", "TSLA"]
        results = agent.detect_levels_batch(symbols, use_parallel=True)
        
        assert len(results) == len(symbols), "Should process all symbols"
        assert all(s in results for s in symbols), "Should have results for all symbols"
