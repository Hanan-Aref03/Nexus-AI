"""Sample telemetry batches used by docs, tests, and local demos."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domains.telemetry.schemas import (
    TelemetryIngestRequest,
    TelemetryResource,
    TelemetrySeverity,
    TelemetrySignalIn,
    TelemetrySignalKind,
    TelemetrySourceType,
)


def build_demo_batch(source_type: TelemetrySourceType = TelemetrySourceType.sample) -> TelemetryIngestRequest:
    """Build a deterministic sample batch that demonstrates the data model."""

    observed_at = datetime(2026, 6, 9, 17, 0, tzinfo=timezone.utc)
    return TelemetryIngestRequest(
        source_name="local-demo",
        source_type=source_type,
        batch_label="phase-1-demo",
        signals=[
            TelemetrySignalIn(
                signal_id="sig-001",
                kind=TelemetrySignalKind.log,
                observed_at=observed_at,
                summary="Checkout API emitted repeated 500 responses",
                description="The sample batch mirrors the kind of issue the platform should eventually explain.",
                severity=TelemetrySeverity.error,
                resource=TelemetryResource(
                    service_name="checkout-api",
                    cluster_name="payments-prod",
                    workload_name="checkout-deployment",
                    namespace="payments",
                    resource_type="kubernetes_pod",
                    resource_name="checkout-api-7f6d9c4b",
                    cloud_provider="aws",
                    region="us-east-1",
                ),
                attributes={
                    "status_code": 500,
                    "request_count": 42,
                    "window_seconds": 5,
                },
                payload={
                    "message": "upstream dependency timed out",
                    "trace_id": "trace-abc-123",
                },
            ),
            TelemetrySignalIn(
                signal_id="sig-002",
                kind=TelemetrySignalKind.metric,
                observed_at=observed_at,
                summary="Redis memory usage crossed the warning threshold",
                severity=TelemetrySeverity.warning,
                resource=TelemetryResource(
                    service_name="redis-cache",
                    cluster_name="payments-prod",
                    workload_name="redis-statefulset",
                    namespace="payments",
                    resource_type="kubernetes_statefulset",
                    resource_name="redis-cache-0",
                    cloud_provider="aws",
                    region="us-east-1",
                ),
                attributes={
                    "memory_utilization": 0.87,
                    "threshold": 0.80,
                },
                payload={
                    "metric_name": "container_memory_working_set_bytes",
                    "value": 861234567,
                },
            ),
        ],
    )

