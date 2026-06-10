"""Source adapters available in the PR1 foundation."""

from app.domains.telemetry.adapters.base import AdapterNotReadyError, AdapterRegistry, TelemetrySourceAdapter
from app.domains.telemetry.adapters.cloudwatch import CloudWatchTelemetryAdapter
from app.domains.telemetry.adapters.openobserve import OpenObserveTelemetryAdapter
from app.domains.telemetry.adapters.otlp import OtlpTelemetryAdapter
from app.domains.telemetry.adapters.sample import SampleTelemetryAdapter

__all__ = [
    "AdapterNotReadyError",
    "AdapterRegistry",
    "TelemetrySourceAdapter",
    "CloudWatchTelemetryAdapter",
    "OpenObserveTelemetryAdapter",
    "OtlpTelemetryAdapter",
    "SampleTelemetryAdapter",
]

