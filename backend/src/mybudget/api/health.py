"""
Health check and metrics endpoints.

Provides endpoints for monitoring application health and
Prometheus metrics collection.
"""
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str = "1.0.0"
    checks: dict[str, Any]


class ComponentHealth(BaseModel):
    """Individual component health status."""

    status: str
    latency_ms: float | None = None
    error: str | None = None


async def check_database(db: AsyncSession) -> ComponentHealth:
    """Check database connectivity and latency."""
    start = datetime.now(UTC)
    try:
        await db.execute(text("SELECT 1"))
        latency = (datetime.now(UTC) - start).total_seconds() * 1000
        return ComponentHealth(status="healthy", latency_ms=round(latency, 2))
    except Exception as e:
        return ComponentHealth(status="unhealthy", error=str(e))


@router.get("", response_model=HealthStatus)
@router.get("/", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthStatus:
    """
    Health check endpoint.

    Returns the overall health status of the application and its dependencies.
    Used by load balancers, Kubernetes probes, and monitoring systems.

    Returns:
        HealthStatus: Current health status with component details.
    """
    db_health = await check_database(db)

    # Determine overall status
    all_healthy = db_health.status == "healthy"
    overall_status = "healthy" if all_healthy else "degraded"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now(UTC).isoformat(),
        checks={
            "database": db_health.model_dump(),
        },
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    Readiness probe endpoint.

    Returns 200 if the application is ready to serve traffic.
    Used by Kubernetes readiness probes.
    """
    db_health = await check_database(db)
    if db_health.status != "healthy":
        return {"status": "not ready", "reason": "database unavailable"}
    return {"status": "ready"}


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe endpoint.

    Returns 200 if the application is running.
    Used by Kubernetes liveness probes.
    """
    return {"status": "alive"}
