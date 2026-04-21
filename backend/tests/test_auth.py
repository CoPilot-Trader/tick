"""
Tests for authentication and authorization middleware.
"""

import os


def test_dev_mode_no_auth_required(client):
    """In dev mode (TICK_AUTH_ENABLED=false), no API key needed."""
    response = client.get("/health")
    assert response.status_code == 200


def test_dev_mode_api_endpoints_accessible(client):
    """API endpoints work without auth in dev mode."""
    response = client.get("/api/v1/forecast/health")
    assert response.status_code == 200


def test_auth_enabled_rejects_no_key(auth_client):
    """When auth is enabled, requests without API key get 401."""
    response = auth_client.get("/api/v1/forecast/health")
    assert response.status_code == 401
    assert "Missing API key" in response.json()["detail"]


def test_auth_enabled_rejects_bad_key(auth_client):
    """When auth is enabled, invalid API key gets 403."""
    response = auth_client.get(
        "/api/v1/forecast/health",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 403
    assert "Invalid API key" in response.json()["detail"]


def test_auth_enabled_accepts_valid_key(auth_client):
    """When auth is enabled, valid API key passes."""
    response = auth_client.get(
        "/api/v1/forecast/health",
        headers={"X-API-Key": "test-key-123"},
    )
    assert response.status_code == 200


def test_auth_via_query_param(auth_client):
    """API key can be passed as query parameter."""
    response = auth_client.get(
        "/api/v1/forecast/health?api_key=test-key-123",
    )
    assert response.status_code == 200


def test_health_endpoint_bypasses_auth(auth_client):
    """Health endpoint should work without auth even when enabled."""
    response = auth_client.get("/health")
    assert response.status_code == 200
