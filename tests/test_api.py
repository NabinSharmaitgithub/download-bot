from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestFastAPIEndpoints:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_ready_endpoint(self, client):
        response = await client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text

    @pytest.mark.asyncio
    async def test_api_info_endpoint(self, client):
        response = await client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Download Bot API"
        assert data["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_404_endpoint(self, client):
        response = await client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_app_exception_handler(self, client):
        from app.core.exceptions import ValidationError

        with patch("app.api.routes.api_info", side_effect=ValidationError("Test validation error")):
            response = await client.get("/api/info")
            assert response.status_code == 400
            data = response.json()
            assert data["error"]["code"] == "VALIDATION_ERROR"
            assert data["error"]["message"] == "Test validation error"

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self, client):
        with patch("app.api.routes.api_info", side_effect=Exception("Internal error")):
            response = await client.get("/api/info")
            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "INTERNAL_ERROR"