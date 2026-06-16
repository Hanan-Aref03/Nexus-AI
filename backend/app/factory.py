"""Application factory for tests, local development, and Uvicorn."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import health_router
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import build_engine, build_session_factory, close_engine
from app.core.middleware import OpenTelemetryMiddleware
from app.core.guardrails import build_evaluation_engine, build_guardrail_engine
from app.core.migrations import upgrade_database
from app.core.telemetry import configure_telemetry
from app.core.secrets import build_runtime_secrets
from app.integrations.copilot import build_copilot_provider_chain
from app.integrations.slack import build_slack_connector
from app.domains.telemetry.adapters import (
    AdapterRegistry,
    CloudWatchTelemetryAdapter,
    OpenObserveTelemetryAdapter,
    OtlpTelemetryAdapter,
    SampleTelemetryAdapter,
)


def build_adapter_registry() -> AdapterRegistry:
    """Create the PR1 adapter registry with ready and planned connectors."""

    return AdapterRegistry(
        adapters=[
            SampleTelemetryAdapter(),
            OtlpTelemetryAdapter(),
            CloudWatchTelemetryAdapter(),
            OpenObserveTelemetryAdapter(),
        ]
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application with explicit startup/shutdown hooks."""

    active_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Prepare persistence and tracing once the application starts."""

        app.state.settings = active_settings
        app.state.runtime_secrets = build_runtime_secrets(active_settings)
        app.state.adapter_registry = build_adapter_registry()
        app.state.guardrail_engine = build_guardrail_engine(active_settings.guardrails_enabled)
        app.state.evaluation_engine = build_evaluation_engine(active_settings.ragas_enabled)
        app.state.copilot_provider_chain = build_copilot_provider_chain(active_settings)
        app.state.slack_connector = build_slack_connector(active_settings)
        app.state.database_ready = False
        app.state.database_error = None

        configure_telemetry(active_settings)

        engine = build_engine(active_settings.database_url, echo=active_settings.database_echo)
        app.state.engine = engine
        app.state.session_factory = build_session_factory(engine)

        try:
            upgrade_database(active_settings.database_url)
            app.state.database_ready = True
        except Exception as exc:  # pragma: no cover - exercised when DB is unavailable
            app.state.database_error = str(exc)

        try:
            yield
        finally:
            close_engine(engine)

    app = FastAPI(
        title=active_settings.project_name,
        version=active_settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_allow_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(OpenTelemetryMiddleware)
    app.include_router(health_router)
    app.include_router(api_router)
    return app
