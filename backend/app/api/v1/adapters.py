"""Adapter discovery endpoint."""

from fastapi import APIRouter, Request

from app.domains.telemetry.schemas import TelemetryAdapterList

adapters_router = APIRouter(prefix="/adapters", tags=["adapters"])


@adapters_router.get("/", response_model=TelemetryAdapterList)
def list_adapters(request: Request) -> TelemetryAdapterList:
    """Expose the currently supported and planned source adapters."""

    return TelemetryAdapterList(adapters=request.app.state.adapter_registry.capabilities())
