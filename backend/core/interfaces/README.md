# Agent Interfaces

This directory contains interface definitions that all agents must implement.

## BaseAgent

All agents must inherit from `BaseAgent` and implement:
- `initialize()` - Initialize the agent
- `process(symbol, params)` - Main processing method
- `health_check()` - Health check method

## Usage

```python
from core.interfaces.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def initialize(self):
        # Your initialization code
        self.initialized = True
        return True
    
    def process(self, symbol: str, params: Optional[Dict] = None):
        # Your processing logic
        return {"result": "data"}
    
    def health_check(self):
        return {"status": "healthy"}
```

## Interface Contracts

See [Component Dependencies](../../../docs/COMPONENT_DEPENDENCIES.md) for specific interface contracts for each agent.

