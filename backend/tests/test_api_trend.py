"""
Tests for trend classification API endpoints.
"""

from tests.conftest import skip_if_optional_dep_missing


def test_trend_classification(client):
    """Test trend classification endpoint."""
    response = client.get("/api/v1/trend/AAPL?timeframe=1d")
    skip_if_optional_dep_missing(response)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["symbol"] == "AAPL"
    assert "signal" in data
    assert data["signal"] in ("BUY", "SELL", "HOLD")
    assert "probabilities" in data
    assert "confidence" in data


def test_trend_probabilities_sum(client):
    """Test that trend probabilities sum to ~1.0."""
    response = client.get("/api/v1/trend/AAPL?timeframe=1d")
    data = response.json()
    probs = data.get("probabilities", {})
    if probs:
        total = sum(probs.values())
        assert 0.95 <= total <= 1.05
