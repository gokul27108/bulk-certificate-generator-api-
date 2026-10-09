"""Tests for health check and root endpoints."""

from unittest.mock import patch


def test_health_check_healthy(client):
    """GET /health returns 200 and healthy status when database is reachable."""
    with patch("app.api.routes.health.check_database_connection", return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


def test_health_check_degraded(client):
    """GET /health returns 503 when database is unreachable."""
    with patch("app.api.routes.health.check_database_connection", return_value=False):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"


def test_root_endpoint(client):
    """GET / returns API information and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data
