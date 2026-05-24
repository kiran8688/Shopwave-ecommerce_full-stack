# backend/tests/test_endpoints.py
# ─────────────────────────────────────────────────────────────────────────────
# Core FastAPI API Endpoint & Configuration unit tests.
# These verify routing trees, configuration properties, and metadata integrity.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_root_ping():
    """Verify that the base server root ping returns valid metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["status"] == "healthy"


def test_health_check():
    """Verify that the health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()


def test_settings_load():
    """Verify settings properties load correctly with expected values."""
    assert settings.APP_NAME == "ShopWave E-Commerce API"
    assert settings.API_V1_PREFIX == "/api/v1"
