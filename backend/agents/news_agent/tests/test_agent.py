"""
Unit tests for News Agent.
"""

import pytest
from agents.news_agent.agent import NewsAgent


class TestNewsAgent:
    """Test cases for News Agent."""
    
    def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = NewsAgent()
        assert agent.name == "news_agent"
        assert agent.initialized == False
    
    def test_agent_health_check(self):
        """Test agent health check."""
        agent = NewsAgent()
        health = agent.health_check()
        assert "status" in health
        assert "agent" in health
        assert health["agent"] == "news_agent"
    
    def test_agent_info(self):
        """Test agent info method."""
        agent = NewsAgent()
        info = agent.get_info()
        assert info["name"] == "news_agent"
        assert "version" in info
        assert "timestamp" in info

