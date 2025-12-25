"""
Unit tests for Feature Agent.
"""

import pytest
from agents.feature_agent.agent import FeatureAgent


class TestFeatureAgent:
    """Test cases for Feature Agent."""
    
    def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = FeatureAgent()
        assert agent.name == "feature_agent"
        assert agent.initialized == False
    
    def test_agent_health_check(self):
        """Test agent health check."""
        agent = FeatureAgent()
        health = agent.health_check()
        assert "status" in health
        assert "agent" in health
        assert health["agent"] == "feature_agent"
    
    def test_agent_info(self):
        """Test agent info method."""
        agent = FeatureAgent()
        info = agent.get_info()
        assert info["name"] == "feature_agent"
        assert "version" in info
        assert "timestamp" in info

