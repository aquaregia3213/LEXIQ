import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /api/health returns HTTP 200 and expected payload structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Legal AI Contract Intelligence API"
    assert "version" in data
    assert "timestamp" in data
    assert "database" in data
    assert "status" in data["database"]


def test_root_redirect():
    """Verify root route redirects to OpenAPI documentation."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/docs"
