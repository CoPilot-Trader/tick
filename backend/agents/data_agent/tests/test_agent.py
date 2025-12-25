"""
Unit tests for Data Agent.
"""

import pytest
from agents.data_agent.agent import DataAgent


class TestDataAgent:
    """Test cases for Data Agent."""
    
    def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = DataAgent()
        assert agent.name == "data_agent"
        assert agent.initialized == False
    
    def test_agent_health_check(self):
        """Test agent health check."""
        agent = DataAgent()
        health = agent.health_check()
        assert "status" in health
        assert "agent" in health
        assert health["agent"] == "data_agent"
    
    def test_agent_info(self):
        """Test agent info method."""
        agent = DataAgent()
        info = agent.get_info()
        assert info["name"] == "data_agent"
        assert "version" in info
        assert "timestamp" in info

