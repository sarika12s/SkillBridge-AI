"""Tests for system health and root metadata endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "SkillBridge AI"
    assert "health" in data
    assert "documentation" in data


def test_health_check_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "SkillBridge AI"
    assert data["api_version"] == "v1"
    assert "database" in data
