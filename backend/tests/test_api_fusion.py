"""
Tests for fusion signal API endpoints.
"""


def test_fusion_health(client):
    response = client.get("/api/v1/fusion/health")
    assert response.status_code == 200


def test_quick_fusion_signal(client):
    """Test quick fusion signal endpoint."""
    response = client.get("/api/v1/fusion/AAPL/quick")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["symbol"] == "AAPL"
    assert "signal" in data
    assert data["signal"] in ("BUY", "SELL", "HOLD")
    assert "confidence" in data
    assert 0 <= data["confidence"] <= 1
    assert "fused_score" in data


def test_fusion_signal_has_components(client):
    """Test that fusion signal includes component details."""
    response = client.get("/api/v1/fusion/AAPL/quick")
    data = response.json()
    assert "components" in data
    components = data["components"]
    assert isinstance(components, dict)


def test_fusion_signal_has_reasoning(client):
    """Test that fusion signal includes reasoning."""
    response = client.get("/api/v1/fusion/AAPL/quick")
    data = response.json()
    assert "reasoning" in data
    assert isinstance(data["reasoning"], str)
    assert len(data["reasoning"]) > 0


def test_fusion_weights(client):
    """Test weights endpoint."""
    response = client.get("/api/v1/fusion/weights")
    assert response.status_code == 200
    data = response.json()
    assert "weights" in data


def test_fusion_components_status(client):
    """Test components status endpoint."""
    response = client.get("/api/v1/fusion/components/status")
    assert response.status_code == 200


def test_multi_timeframe_signal(client):
    """Test multi-timeframe signal endpoint."""
    response = client.get("/api/v1/fusion/AAPL/multi-timeframe")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "timeframes" in data
    assert "agreement" in data
    assert data["agreement"] in ("ALIGNED", "CONFLICTING")
