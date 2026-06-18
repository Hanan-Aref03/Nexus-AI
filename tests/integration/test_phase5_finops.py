"""Integration smoke test for the Phase 5 FinOps insights endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.config import Settings
from app.factory import create_app
from app.domains.telemetry.sample_data import build_demo_batch


def build_test_settings() -> Settings:
    """Build a file-backed SQLite configuration for the FinOps integration test."""

    repo_root = Path(__file__).resolve().parents[2]
    database_path = repo_root / ".tmp" / "integration" / "phase5-finops.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        candidate = database_path.with_name(f"{database_path.name}{suffix}")
        if candidate.exists():
            candidate.unlink()
    return Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{database_path}",
        auth_signing_key="integration-test-signing-key",
        otel_console_exporter=False,
    )


def test_finops_endpoint_derives_savings_from_workspace_pressure() -> None:
    """Smoke test telemetry ingestion, detection, and FinOps derivation."""

    app = create_app(build_test_settings())

    with TestClient(app) as client:
        assert hasattr(app.state, "slack_connector")

        finops_token = create_access_token(
            app.state.runtime_secrets,
            subject="tester-finops",
            tenant_id="payments",
            roles=("telemetry:read", "telemetry:write", "analysis:read", "analysis:write", "alerts:read"),
            issuer=app.state.settings.auth_token_issuer,
            audience=app.state.settings.auth_token_audience,
        )
        analysis_only_token = create_access_token(
            app.state.runtime_secrets,
            subject="tester-analysis",
            tenant_id="payments",
            roles=("telemetry:read", "telemetry:write", "analysis:write"),
            issuer=app.state.settings.auth_token_issuer,
            audience=app.state.settings.auth_token_audience,
        )
        headers = {"Authorization": f"Bearer {finops_token}"}
        analysis_headers = {"Authorization": f"Bearer {analysis_only_token}"}

        ingest_response = client.post(
            "/api/v1/telemetry/ingest",
            json=build_demo_batch().model_dump(mode="json"),
            headers=headers,
        )
        assert ingest_response.status_code == 201

        run_response = client.post("/api/v1/analysis/run?limit=50", headers=headers)
        assert run_response.status_code == 200

        forbidden = client.get("/api/v1/finops/insights?limit=50", headers=analysis_headers)
        assert forbidden.status_code == 403

        finops_response = client.get("/api/v1/finops/insights?limit=50", headers=headers)
        assert finops_response.status_code == 200
        body = finops_response.json()

        assert body["mode"] == "live"
        assert body["estimated_monthly_savings"] > 0
        assert body["opportunity_count"] >= 1
        assert body["forecast_count"] >= 1
        assert body["top_scope"]
        assert body["opportunities"][0]["headline"]
        assert body["forecasts"][0]["headline"]
