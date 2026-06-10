"""OpenTelemetry bootstrap for the backend.

PR1 uses the official OpenTelemetry API/SDK packages directly so the service
can emit spans without paying for a third-party observability backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

try:  # pragma: no cover - exporter support is environment-specific
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
except ImportError:  # pragma: no cover - the SDK is still useful without console export
    ConsoleSpanExporter = None  # type: ignore[assignment]
    SimpleSpanProcessor = None  # type: ignore[assignment]


@dataclass(frozen=True)
class TelemetryBootstrapResult:
    """Small status object used by docs and readiness checks."""

    configured: bool
    exporter: str


_TELEMETRY_CONFIGURED = False


def build_resource(settings: Any) -> Resource:
    """Create the OpenTelemetry resource attached to all spans."""

    return Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
            "nexusai.project": settings.project_name,
        }
    )


def configure_telemetry(settings: Any) -> TelemetryBootstrapResult:
    """Configure OpenTelemetry exactly once for the whole process."""

    global _TELEMETRY_CONFIGURED
    if _TELEMETRY_CONFIGURED:
        return TelemetryBootstrapResult(
            configured=True,
            exporter="already-configured",
        )

    provider = TracerProvider(resource=build_resource(settings))

    exporter_name = "sdk-only"
    if settings.otel_console_exporter and ConsoleSpanExporter and SimpleSpanProcessor:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        exporter_name = "console"

    trace.set_tracer_provider(provider)
    _TELEMETRY_CONFIGURED = True
    return TelemetryBootstrapResult(configured=True, exporter=exporter_name)


@lru_cache(maxsize=1)
def get_tracer() -> trace.Tracer:
    """Return a shared tracer for backend spans."""

    return trace.get_tracer("nexusai.backend")

