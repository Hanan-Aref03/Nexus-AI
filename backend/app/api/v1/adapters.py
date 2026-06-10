"""Adapter discovery endpoint."""

from fastapi import APIRouter, Depends, Request

from app.core.auth import SecurityPrincipal, require_roles
from app.domains.telemetry.schemas import TelemetryAdapterList

adapters_router = APIRouter(prefix="/adapters", tags=["adapters"])


@adapters_router.get("/", response_model=TelemetryAdapterList)
def list_adapters(
    request: Request,
    principal: SecurityPrincipal = Depends(require_roles("telemetry:read")),
) -> TelemetryAdapterList:
    """Expose the currently supported and planned source adapters."""

    _ = principal
    return TelemetryAdapterList(adapters=request.app.state.adapter_registry.capabilities())
