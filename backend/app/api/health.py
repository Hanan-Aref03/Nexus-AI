"""Root health and readiness routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import ping_database
from app.domains.telemetry.schemas import HealthResponse, ReadyDatabaseStatus, ReadyResponse

health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    """Liveness endpoint that does not depend on downstream services."""

    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.otel_service_name,
        version=settings.app_version,
        environment=settings.environment,
        telemetry="open-telemetry-sdk",
    )


@health_router.get("/ready", response_model=ReadyResponse)
def ready(request: Request) -> ReadyResponse:
    """Readiness endpoint that verifies the database and adapter registry."""

    settings = request.app.state.settings
    adapters = request.app.state.adapter_registry.capabilities()

    try:
        database = ping_database(request.app.state.engine)
        database_status = ReadyDatabaseStatus(status="ready", checked_at=database["checked_at"])
        overall_status: str = "ready"
    except SQLAlchemyError as exc:
        database_status = ReadyDatabaseStatus(status="degraded", error=str(exc))
        overall_status = "degraded"

    if overall_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ReadyResponse(
                status="degraded",
                service=settings.otel_service_name,
                database=database_status,
                adapters=adapters,
            ).model_dump(mode="json"),
        )

    return ReadyResponse(
        status="ready",
        service=settings.otel_service_name,
        database=database_status,
        adapters=adapters,
    )
