"""Integration smoke test for the PR1 foundation."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app
from app.domains.telemetry.sample_data import build_demo_batch


def build_test_settings() -> Settings:
    """Build a file-backed SQLite configuration for isolated tests."""

    repo_root = Path(__file__).resolve().parents[2]
    database_path = repo_root / ".tmp" / "integration" / "nexusai-test.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        candidate = database_path.with_name(f"{database_path.name}{suffix}")
        if candidate.exists():
            candidate.unlink()
    return Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{database_path}",
        otel_console_exporter=False,
    )


def test_health_readiness_and_ingest_flow() -> None:
    """Smoke test the app from health checks through signal persistence."""

    app = create_app(build_test_settings())

    with TestClient(app) as client:
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "ok"

        ready_response = client.get("/ready")
        assert ready_response.status_code == 200
        ready_body = ready_response.json()
        assert ready_body["status"] == "ready"
        assert ready_body["database"]["status"] == "ready"
        assert len(ready_body["adapters"]) == 4

        adapters_response = client.get("/api/v1/adapters")
        assert adapters_response.status_code == 200
        adapters_body = adapters_response.json()
        assert [item["status"] for item in adapters_body["adapters"]] == ["ready", "ready", "planned", "planned"]

        batch = build_demo_batch()
        ingest_response = client.post("/api/v1/telemetry/ingest", json=batch.model_dump(mode="json"))
        assert ingest_response.status_code == 201
        ingest_body = ingest_response.json()
        assert ingest_body["accepted_signals"] == 2
        assert ingest_body["stored_signals"] == 2
        assert ingest_body["record_ids"] == ["sig-001", "sig-002"]

        signals_response = client.get("/api/v1/telemetry/signals?limit=10")
        assert signals_response.status_code == 200
        signals = signals_response.json()
        assert len(signals) == 2
        assert signals[0]["resource"]["service_name"] in {"checkout-api", "redis-cache"}
