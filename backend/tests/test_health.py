import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify root endpoint returns app metadata."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == settings.APP_NAME
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/v1/health"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify health endpoint returns status ok and correct version."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == settings.APP_NAME
        assert data["version"] == settings.APP_VERSION
        assert data["environment"] == settings.ENVIRONMENT
