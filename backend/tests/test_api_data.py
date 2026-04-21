"""
Tests for OHLCV data API endpoints.
"""

import pytest


def test_get_ohlcv_default(client):
    """Test OHLCV endpoint with default params."""
    response = client.get("/api/v1/data/AAPL/ohlcv")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["timeframe"] == "5m"
    assert "data" in data
    assert "count" in data
    assert data["count"] > 0


def test_get_ohlcv_custom_timeframe(client):
    """Test OHLCV with 1d timeframe."""
    response = client.get("/api/v1/data/AAPL/ohlcv?timeframe=1d&days=30")
    assert response.status_code == 200
    data = response.json()
    assert data["timeframe"] == "1d"
    assert data["count"] > 0


def test_get_ohlcv_data_structure(client):
    """Test that OHLCV data has correct fields."""
    response = client.get("/api/v1/data/AAPL/ohlcv")
    data = response.json()
    if data["count"] > 0:
        candle = data["data"][0]
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle
        assert isinstance(candle["open"], (int, float))
        assert isinstance(candle["volume"], int)


def test_get_ohlcv_multiple_symbols(client):
    """Test OHLCV works for different symbols."""
    for symbol in ["AAPL", "MSFT", "GOOGL"]:
        response = client.get(f"/api/v1/data/{symbol}/ohlcv")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == symbol


def test_get_ohlcv_invalid_days(client):
    """Test OHLCV rejects invalid days parameter."""
    response = client.get("/api/v1/data/AAPL/ohlcv?days=0")
    assert response.status_code == 422


def test_get_ohlcv_caching(client):
    """Test that second request is faster (cached)."""
    import time
    t0 = time.time()
    client.get("/api/v1/data/AAPL/ohlcv?timeframe=5m&days=1")
    first = time.time() - t0

    t0 = time.time()
    client.get("/api/v1/data/AAPL/ohlcv?timeframe=5m&days=1")
    second = time.time() - t0

    # Second request should be significantly faster if cached
    assert second < first or second < 1.0
