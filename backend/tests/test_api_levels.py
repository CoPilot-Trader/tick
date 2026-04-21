"""
Tests for support/resistance levels API endpoints.
"""


def test_levels_health(client):
    response = client.get("/api/v1/levels/health")
    assert response.status_code == 200


def test_get_levels(client):
    """Test levels endpoint returns S/R levels."""
    response = client.get("/api/v1/levels/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "symbol" in data
    assert "support_levels" in data
    assert "resistance_levels" in data
    assert isinstance(data["support_levels"], list)
    assert isinstance(data["resistance_levels"], list)


def test_levels_have_strength(client):
    """Test that levels include strength scores."""
    response = client.get("/api/v1/levels/AAPL")
    data = response.json()
    for level in data.get("support_levels", []):
        assert "price" in level
        assert "strength" in level
        assert isinstance(level["price"], (int, float))
        assert 0 <= level["strength"] <= 100


def test_levels_max_levels_param(client):
    """Test max_levels parameter."""
    response = client.get("/api/v1/levels/AAPL?max_levels=2")
    data = response.json()
    assert len(data.get("support_levels", [])) <= 2
    assert len(data.get("resistance_levels", [])) <= 2
