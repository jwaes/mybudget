"""
Tests for FastAPI application startup and configuration.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from mybudget.main import app


class TestAppStartup:
    """Tests for FastAPI app startup and basic configuration."""

    def test_app_title(self) -> None:
        """Test that app has correct title."""
        assert app.title == "MyBudget API"

    def test_app_version(self) -> None:
        """Test that app has a version."""
        assert app.version == "0.1.0"

    def test_app_description(self) -> None:
        """Test that app has a description."""
        assert "spending targets" in app.description.lower()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client: AsyncClient) -> None:
        """Test that /health returns 200 OK."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(
        self, client: AsyncClient
    ) -> None:
        """Test that /health returns healthy status."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestOpenAPISchema:
    """Tests for OpenAPI schema availability."""

    @pytest.mark.asyncio
    async def test_openapi_schema_available(self, client: AsyncClient) -> None:
        """Test that OpenAPI schema is available at /openapi.json."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    @pytest.mark.asyncio
    async def test_docs_available(self, client: AsyncClient) -> None:
        """Test that Swagger UI is available at /docs."""
        response = await client.get("/docs")
        assert response.status_code == 200
        # Should return HTML
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_redoc_available(self, client: AsyncClient) -> None:
        """Test that ReDoc is available at /redoc."""
        response = await client.get("/redoc")
        assert response.status_code == 200
        # Should return HTML
        assert "text/html" in response.headers["content-type"]


class TestAPIRouters:
    """Tests for API router registration."""

    @pytest.mark.asyncio
    async def test_auth_routes_registered(self, client: AsyncClient) -> None:
        """Test that auth routes are registered."""
        response = await client.get("/openapi.json")
        data = response.json()
        paths = data["paths"]

        # Check auth endpoints exist
        assert "/api/register" in paths
        assert "/api/login" in paths
        assert "/api/logout" in paths
        assert "/api/me" in paths

    @pytest.mark.asyncio
    async def test_api_tags_configured(self, client: AsyncClient) -> None:
        """Test that API tags are configured for documentation."""
        response = await client.get("/openapi.json")
        data = response.json()
        paths = data.get("paths", {})

        # Collect all tags from path operations
        all_tags: set[str] = set()
        for path_data in paths.values():
            for method_data in path_data.values():
                if isinstance(method_data, dict) and "tags" in method_data:
                    all_tags.update(method_data["tags"])

        # Check expected tags exist (from registered routers)
        # Auth tag should exist from auth endpoints
        assert "Auth" in all_tags


class TestCORSConfiguration:
    """Tests for CORS middleware configuration."""

    @pytest.mark.asyncio
    async def test_cors_preflight_request(self, client: AsyncClient) -> None:
        """Test that CORS preflight requests work."""
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should return 200 for valid CORS preflight
        assert response.status_code == 200
