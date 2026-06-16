"""Version 1 router composition."""

from fastapi import APIRouter

from app.api.v1.copilot import copilot_router
from app.api.v1.alerts import alerts_router
from app.api.v1.analysis import analysis_router
from app.api.v1.adapters import adapters_router
from app.api.v1.telemetry import telemetry_router

v1_router = APIRouter()
v1_router.include_router(copilot_router)
v1_router.include_router(alerts_router)
v1_router.include_router(analysis_router)
v1_router.include_router(adapters_router)
v1_router.include_router(telemetry_router)
