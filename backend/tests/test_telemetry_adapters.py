"""Unit tests for the PR1 adapter registry and sample normalization."""

from __future__ import annotations

from app.domains.telemetry.adapters import (
    AdapterRegistry,
    CloudWatchTelemetryAdapter,
    OpenObserveTelemetryAdapter,
    OtlpTelemetryAdapter,
    SampleTelemetryAdapter,
)
from app.domains.telemetry.sample_data import build_demo_batch
from app.domains.telemetry.schemas import TelemetrySourceType


def test_sample_adapter_passes_through_normalized_signals() -> None:
    """The sample adapter should preserve the normalized telemetry batch."""

    batch = build_demo_batch(source_type=TelemetrySourceType.sample)
    registry = AdapterRegistry([SampleTelemetryAdapter(), OtlpTelemetryAdapter()])

    adapter = registry.get(batch.source_type)
    normalized = adapter.normalize(batch)

    assert len(normalized) == 2
    assert normalized[0].resource.service_name == "checkout-api"
    assert adapter.capability().deployment_model == "free-local"


def test_registry_exposes_free_local_and_planned_sources() -> None:
    """The registry should surface both ready and planned source families."""

    registry = AdapterRegistry(
        [
            SampleTelemetryAdapter(),
            OtlpTelemetryAdapter(),
            CloudWatchTelemetryAdapter(),
            OpenObserveTelemetryAdapter(),
        ]
    )
    capabilities = registry.capabilities()

    assert [item.status for item in capabilities] == ["ready", "ready", "planned", "planned"]
    assert {item.source_type.value for item in capabilities} == {
        "sample",
        "otlp",
        "cloudwatch",
        "openobserve",
    }
