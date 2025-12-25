"""
Base interface for all agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseAgent(ABC):
    """
    Base class that all agents must implement.
    
    This ensures consistency across all agents and provides
    a standard interface for the orchestrator.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.
        
        Args:
            name: Agent name/identifier
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the agent (load models, connect to APIs, etc.).
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main processing method for the agent.
        
        Args:
            symbol: Stock symbol to process
            params: Optional parameters for processing
            
        Returns:
            Dictionary containing agent results
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check agent health and status.
        
        Returns:
            Dictionary with health status information
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get agent information.
        
        Returns:
            Dictionary with agent metadata
        """
        return {
            "name": self.name,
            "initialized": self.initialized,
            "version": getattr(self, "version", "1.0.0"),
            "timestamp": datetime.utcnow().isoformat()
        }

