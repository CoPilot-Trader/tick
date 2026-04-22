"""
Tests for the Signal Bridge router (Level Rejection + PCR Shock endpoints).
"""


def test_signal_bridge_health(client):
    r = client.get("/api/v1/signals/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "level_rejection" in data["datasets"]
    assert "pcr_shock" in data["datasets"]


def test_level_rejection_spy(client):
    r = client.get("/api/v1/signals/level-rejection/SPY")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["ticker"] == "SPY"
    assert isinstance(data["signals"], list)
    assert data["count"] == len(data["signals"])
    if data["count"] > 0:
        sig = data["signals"][0]
        assert "ticker" in sig
        assert "signal_time" in sig
        assert "level_type" in sig
        assert "level_price" in sig
        assert "entry_price" in sig
        assert "target1_price" in sig
        assert "stop_price" in sig
        assert "side" in sig
        assert sig["side"] == "CALL"


def test_level_rejection_unknown_ticker(client):
    r = client.get("/api/v1/signals/level-rejection/ZZZZZ")
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_level_rejection_win_rate(client):
    r = client.get("/api/v1/signals/level-rejection/SPY")
    data = r.json()
    if data["count"] > 0:
        assert data["win_rate"] is not None
        assert 0 <= data["win_rate"] <= 1


def test_pcr_shock_raw(client):
    r = client.get("/api/v1/signals/pcr-shock/SPY")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert isinstance(data["signals"], list)
    if data["count"] > 0:
        sig = data["signals"][0]
        assert "ticker" in sig
        assert "signal_ts" in sig
        assert "spot_at_signal" in sig
        assert "signal_type" in sig


def test_pcr_shock_backtrack(client):
    """Backtrack endpoint returns PredictionHistoryEntry-shaped data."""
    r = client.get("/api/v1/signals/pcr-shock/SPY/backtrack?limit=50")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "predictions" in data
    assert isinstance(data["predictions"], list)
    if data["count"] > 0:
        entry = data["predictions"][0]
        # Must match PredictionHistoryEntry shape
        assert "predicted_at" in entry
        assert "horizon" in entry
        assert "base_price" in entry
        assert "predicted_price" in entry
        assert "confidence" in entry
        assert "direction" in entry
        assert "target_date" in entry
        assert "source" in entry
        assert entry["source"] == "pcr_shock"
        assert entry["direction"] in ("UP", "DOWN")
        assert 0 < entry["confidence"] <= 1


def test_pcr_shock_backtrack_accuracy(client):
    """Backtrack should include accuracy stats if resolved signals exist."""
    r = client.get("/api/v1/signals/pcr-shock/SPY/backtrack")
    data = r.json()
    if data["count"] > 0 and data.get("accuracy"):
        acc = data["accuracy"]
        assert "mape" in acc
        assert "directional_accuracy" in acc
        assert "total_predictions" in acc
        assert "resolved" in acc


def test_signal_refresh_endpoint(client):
    """Refresh endpoint should exist (may fail if GCS lib not installed)."""
    r = client.post("/api/v1/signals/refresh")
    # 200 (success), 500 (GCS unreachable / no credentials), or 501 (lib not installed)
    assert r.status_code in (200, 500, 501)
