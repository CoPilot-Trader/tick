"""
Unit tests for Price Prediction Agent.
"""

import pytest
from agents.price_prediction_agent.agent import PricePredictionAgent


class TestPricePredictionAgent:
    """Test cases for Price Prediction Agent."""
    
    def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = PricePredictionAgent()
        assert agent.name == "price_prediction_agent"
        assert agent.initialized == False
    
    def test_agent_health_check(self):
        """Test agent health check."""
        agent = PricePredictionAgent()
        health = agent.health_check()
        assert "status" in health
        assert "agent" in health
        assert health["agent"] == "price_prediction_agent"
    
    def test_agent_info(self):
        """Test agent info method."""
        agent = PricePredictionAgent()
        info = agent.get_info()
        assert info["name"] == "price_prediction_agent"
        assert "version" in info
        assert "timestamp" in info

