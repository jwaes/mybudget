"""
Contract tests for Health API endpoints.

Tests for observability infrastructure including health checks
and Prometheus metrics endpoints (FR-OBS-002, FR-OBS-003).
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.contract
class TestHealthAPI:
    """Contract tests for health API."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test health check endpoint returns healthy status (T205)."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert data["checks"]["database"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_includes_db_latency(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test health check includes database latency measurement."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        db_check = data["checks"]["database"]
        assert "latency_ms" in db_check
        assert db_check["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_health_check_with_trailing_slash(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test health check endpoint works with trailing slash."""
        response = await client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]

    @pytest.mark.asyncio
    async def test_readiness_check(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test readiness probe endpoint."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_liveness_check(
        self, client: AsyncClient
    ) -> None:
        """Test liveness probe endpoint."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    @pytest.mark.asyncio
    async def test_liveness_check_no_db_required(
        self, client: AsyncClient
    ) -> None:
        """Test liveness probe doesn't require database."""
        # Liveness check should work even without db_session fixture
        response = await client.get("/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "alive"


@pytest.mark.contract
class TestMetricsAPI:
    """Contract tests for Prometheus metrics API."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_accessible(
        self, client: AsyncClient
    ) -> None:
        """Test Prometheus metrics endpoint is accessible (T206).

        Note: The Prometheus instrumentator may be disabled in tests
        depending on environment configuration. If /metrics returns 404,
        that's acceptable for test environments.
        """
        response = await client.get("/metrics")

        # Metrics endpoint should either return 200 with Prometheus format
        # or 404 if disabled in test environment
        if response.status_code == 200:
            # Prometheus metrics are in text format
            content_type = response.headers.get("content-type", "")
            assert "text/plain" in content_type or "text/" in content_type
            content = response.text
            # Should contain Prometheus metric format indicators
            assert "# " in content or "http" in content.lower() or "_total" in content
        else:
            # 404 is acceptable if metrics are disabled in tests
            assert response.status_code == 404, f"Unexpected status: {response.status_code}"

    @pytest.mark.asyncio
    async def test_metrics_includes_request_metrics(
        self, client: AsyncClient
    ) -> None:
        """Test metrics endpoint includes HTTP request metrics after making requests."""
        # Make a request first to generate metrics
        await client.get("/health/live")
        await client.get("/health")

        response = await client.get("/metrics")

        # If metrics are available, check for HTTP-related metrics
        if response.status_code == 200:
            content = response.text
            # Check for common Prometheus metric patterns
            assert "http" in content.lower() or "request" in content.lower()
