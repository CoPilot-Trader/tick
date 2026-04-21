"""
Tests for alerts API endpoints.
"""


def test_alerts_health(client):
    response = client.get("/api/v1/alerts/health")
    assert response.status_code == 200


def test_get_alerts(client):
    """Test get alerts endpoint."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


def test_alerts_summary(client):
    """Test alerts summary endpoint."""
    response = client.get("/api/v1/alerts/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_alerts" in data


def test_alert_rules(client):
    """Test alert rules endpoint."""
    response = client.get("/api/v1/alerts/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert isinstance(data["rules"], list)


def test_get_alerts_with_filters(client):
    """Covers the filter-parsing branches."""
    r = client.get("/api/v1/alerts?ticker=AAPL&alert_type=signal&priority=high&unacknowledged_only=true&limit=5")
    assert r.status_code == 200


def test_get_alerts_with_bad_enums(client):
    """Bad enum values should be tolerated (filter falls back to None)."""
    r = client.get("/api/v1/alerts?alert_type=bogus&priority=unknown")
    assert r.status_code == 200


def test_acknowledge_unknown_alert(client):
    r = client.post("/api/v1/alerts/does-not-exist/acknowledge")
    assert r.status_code == 404


def test_acknowledge_all(client):
    r = client.post("/api/v1/alerts/acknowledge-all")
    assert r.status_code == 200
    assert "acknowledged_count" in r.json()


def test_enable_disable_unknown_rule(client):
    assert client.post("/api/v1/alerts/rules/nope/enable").status_code == 404
    assert client.post("/api/v1/alerts/rules/nope/disable").status_code == 404
    assert client.delete("/api/v1/alerts/rules/nope").status_code == 404


def test_enable_disable_known_rule(client):
    r = client.get("/api/v1/alerts/rules")
    rules = r.json().get("rules", [])
    if not rules:
        return
    rule_id = rules[0].get("id") or rules[0].get("rule_id")
    if not rule_id:
        return
    assert client.post(f"/api/v1/alerts/rules/{rule_id}/disable").status_code == 200
    assert client.post(f"/api/v1/alerts/rules/{rule_id}/enable").status_code == 200


def test_clear_alerts(client):
    r = client.delete("/api/v1/alerts")
    assert r.status_code == 200


def test_check_alerts_for_ticker(client):
    payload = {
        "ticker": "AAPL",
        "signal": "BUY",
        "confidence": 0.9,
        "fused_score": 0.8,
        "current_price": 180.0,
    }
    r = client.post("/api/v1/alerts/check/AAPL", json=payload)
    assert r.status_code == 200
