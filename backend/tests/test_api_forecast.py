"""
Tests for price forecast API endpoints.
"""

import json
from pathlib import Path

from tests.conftest import skip_if_optional_dep_missing


def test_forecast_health(client):
    response = client.get("/api/v1/forecast/health")
    assert response.status_code == 200


def test_get_prediction(client):
    """Test prediction endpoint returns valid forecast."""
    response = client.get("/api/v1/forecast/AAPL?horizons=1h&use_baseline=true&use_ensemble=false")
    skip_if_optional_dep_missing(response)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["ticker"] == "AAPL"
    assert "current_price" in data
    assert "predictions" in data
    assert isinstance(data["current_price"], (int, float))
    assert data["current_price"] > 0


def test_prediction_has_horizons(client):
    """Test that predictions include requested horizons."""
    response = client.get("/api/v1/forecast/AAPL?horizons=1h&use_baseline=true&use_ensemble=false")
    skip_if_optional_dep_missing(response)
    data = response.json()
    preds = data.get("predictions", {})
    assert "1h" in preds
    pred_1h = preds["1h"]
    assert "price" in pred_1h
    assert "confidence" in pred_1h
    assert "direction" in pred_1h
    assert pred_1h["direction"] in ("UP", "DOWN", "NEUTRAL")
    assert 0 <= pred_1h["confidence"] <= 1


def test_prediction_confidence_bounds(client):
    """Test prediction includes upper/lower bounds."""
    response = client.get("/api/v1/forecast/AAPL?horizons=1h&use_baseline=true&use_ensemble=false")
    skip_if_optional_dep_missing(response)
    data = response.json()
    pred = data["predictions"]["1h"]
    assert "price_lower" in pred
    assert "price_upper" in pred
    assert pred["price_lower"] <= pred["price"] <= pred["price_upper"]


def test_prediction_logs_to_file(client):
    """Test that predictions are logged for backtracking."""
    resp = client.get("/api/v1/forecast/AAPL?horizons=1h&use_baseline=true&use_ensemble=false")
    skip_if_optional_dep_missing(resp)
    log_path = Path(__file__).parent.parent / "storage" / "prediction_logs" / "AAPL_predictions.json"
    assert log_path.exists()
    entries = json.loads(log_path.read_text())
    assert len(entries) > 0
    last = entries[-1]
    assert "timestamp" in last
    assert "current_price" in last
    assert "predictions" in last


def test_prediction_history(client):
    """Test prediction history endpoint."""
    response = client.get("/api/v1/forecast/AAPL/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["symbol"] == "AAPL"
    assert "predictions" in data
    assert "accuracy" in data
    assert isinstance(data["predictions"], list)


def test_prediction_history_fields(client):
    """Test prediction history entries have correct fields."""
    response = client.get("/api/v1/forecast/AAPL/history?limit=10")
    data = response.json()
    if data["count"] > 0:
        entry = data["predictions"][0]
        assert "predicted_at" in entry
        assert "horizon" in entry
        assert "base_price" in entry
        assert "predicted_price" in entry
        assert "target_date" in entry
        assert "actual_price" in entry
        assert "error_pct" in entry
        assert "direction_correct" in entry


def test_model_info(client):
    """Test model info endpoint."""
    response = client.get("/api/v1/forecast/AAPL/info")
    assert response.status_code == 200
