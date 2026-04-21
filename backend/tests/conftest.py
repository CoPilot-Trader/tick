"""
Shared test fixtures for the TICK test suite.
"""

import os
import pytest
from fastapi.testclient import TestClient

os.environ["TICK_AUTH_ENABLED"] = "false"

from api.main import app


def skip_if_optional_dep_missing(response):
    """Skip the test when the backend signals a missing optional ML dep
    or when upstream data sources are unavailable in the local test env."""
    if response.status_code >= 400:
        detail = ""
        try:
            detail = str(response.json().get("detail", ""))
        except Exception:
            pass
        markers = (
            "not installed", "no module named", "prophet", "lightgbm",
            "xgboost", "tensorflow", "insufficient data", "model not trained",
        )
        if any(m in detail.lower() for m in markers):
            pytest.skip(f"Optional dependency or upstream data unavailable: {detail}")


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def auth_client():
    """Create a test client with auth enabled."""
    os.environ["TICK_AUTH_ENABLED"] = "true"
    os.environ["TICK_API_KEYS"] = "test-key-123"
    yield TestClient(app)
    os.environ["TICK_AUTH_ENABLED"] = "false"
    os.environ.pop("TICK_API_KEYS", None)
