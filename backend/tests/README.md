# Integration Tests

Integration tests for the entire backend system.

## Running Tests

```bash
# All integration tests
pytest tests/

# Specific test file
pytest tests/test_api.py
```

## Test Structure

- `test_api.py` - API endpoint tests
- `test_orchestrator.py` - Orchestrator integration tests
- `test_agents_integration.py` - Cross-agent integration tests

