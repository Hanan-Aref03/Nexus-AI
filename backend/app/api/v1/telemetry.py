"""Telemetry ingestion and inspection routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal, require_roles
from app.core.dependencies import get_adapter_registry, get_session
from app.domains.telemetry.adapters.base import AdapterNotReadyError, AdapterRegistry
from app.domains.telemetry.repository import TelemetryRepository
from app.domains.telemetry.schemas import (
    TelemetryIngestRequest,
    TelemetryIngestResult,
    TelemetrySignalOut,
)
from app.domains.telemetry.service import TelemetryIngestService

telemetry_router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@telemetry_router.post("/ingest", response_model=TelemetryIngestResult, status_code=status.HTTP_201_CREATED)
def ingest_telemetry(
    batch: TelemetryIngestRequest,
    session: Session = Depends(get_session),
    registry: AdapterRegistry = Depends(get_adapter_registry),
    principal: SecurityPrincipal = Depends(require_roles("telemetry:write")),
) -> TelemetryIngestResult:
    """Ingest one batch of normalized telemetry through the adapter seam."""

    service = TelemetryIngestService(adapter_registry=registry, repository=TelemetryRepository(session))
    try:
        return service.ingest(batch, principal=principal)
    except AdapterNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc


@telemetry_router.get("/signals", response_model=list[TelemetrySignalOut])
def list_signals(
    limit: int = 20,
    session: Session = Depends(get_session),
    principal: SecurityPrincipal = Depends(require_roles("telemetry:read")),
) -> list[TelemetrySignalOut]:
    """Return recent stored signals to support local development and demos."""

    repository = TelemetryRepository(session)
    return [
        repository.to_out(record)
        for record in repository.list_recent_signals(principal=principal, limit=limit)
    ]
