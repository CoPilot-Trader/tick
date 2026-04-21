"""
Tests for backtesting API endpoints.
"""


def test_backtest_health(client):
    response = client.get("/api/v1/backtest/health")
    assert response.status_code == 200


def test_quick_backtest(client):
    """Test quick backtest endpoint."""
    response = client.get("/api/v1/backtest/AAPL/quick?days=180")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["symbol"] == "AAPL"
    assert "total_trades" in data
    assert "metrics" in data
    metrics = data["metrics"]
    assert "win_rate" in metrics
    assert "sharpe_ratio" in metrics
    assert "max_drawdown_pct" in metrics or "max_drawdown" in metrics


def test_backtest_config(client):
    """Test backtest config endpoint."""
    response = client.get("/api/v1/backtest/config")
    assert response.status_code == 200
    data = response.json()
    assert "initial_capital" in data or "status" in data


def test_backtest_metrics_valid(client):
    """Test that backtest returns valid metrics."""
    response = client.get("/api/v1/backtest/AAPL/quick?days=180")
    data = response.json()
    if data.get("status") == "success":
        metrics = data["metrics"]
        assert 0 <= metrics["win_rate"] <= 1
        assert isinstance(data["total_trades"], int)
        assert isinstance(metrics["sharpe_ratio"], (int, float))
