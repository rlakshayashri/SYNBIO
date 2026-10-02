from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_index() -> None:
    """Verify that root endpoint returns application metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "SynDataX"
    assert data["health"] == "/api/v1/health"


def test_health_endpoint() -> None:
    """Verify that /api/v1/health returns HTTP 200 and expected payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "SynDataX backend"
    assert "version" in data
