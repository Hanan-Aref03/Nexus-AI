"""Integration smoke test for the Phase 4 alert inbox."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.config import Settings
from app.factory import create_app
from app.domains.telemetry.sample_data import build_demo_batch


def build_test_settings() -> Settings:
    """Build a file-backed SQLite configuration for the alerts integration test."""

    repo_root = Path(__file__).resolve().parents[2]
    database_path = repo_root / ".tmp" / "integration" / "phase4-alerts.db"
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


def test_alert_feed_is_authorized_and_derived_from_analysis_outputs() -> None:
    """Smoke test telemetry ingestion, detection, and alert derivation."""

    app = create_app(build_test_settings())

    with TestClient(app) as client:
        assert hasattr(app.state, "slack_connector")

        alert_token = create_access_token(
            app.state.runtime_secrets,
            subject="tester-alerts",
            tenant_id="payments",
            roles=("telemetry:read", "telemetry:write", "analysis:read", "analysis:write", "alerts:read"),
            issuer=app.state.settings.auth_token_issuer,
            audience=app.state.settings.auth_token_audience,
        )
        analysis_only_token = create_access_token(
            app.state.runtime_secrets,
            subject="tester-analysis",
            tenant_id="payments",
            roles=("telemetry:read", "telemetry:write", "analysis:read", "analysis:write"),
            issuer=app.state.settings.auth_token_issuer,
            audience=app.state.settings.auth_token_audience,
        )
        headers = {"Authorization": f"Bearer {alert_token}"}
        analysis_headers = {"Authorization": f"Bearer {analysis_only_token}"}

        ingest_response = client.post(
            "/api/v1/telemetry/ingest",
            json=build_demo_batch().model_dump(mode="json"),
            headers=headers,
        )
        assert ingest_response.status_code == 201

        run_response = client.post("/api/v1/analysis/run?limit=50", headers=headers)
        assert run_response.status_code == 200

        forbidden = client.get("/api/v1/alerts?limit=10", headers=analysis_headers)
        assert forbidden.status_code == 403

        alerts_response = client.get("/api/v1/alerts?limit=10", headers=headers)
        assert alerts_response.status_code == 200
        body = alerts_response.json()

        assert body["mode"] == "live"
        assert body["summary"]["total"] == 5
        assert body["summary"]["incidents"] == 1
        assert body["summary"]["health"] == 4
        assert body["summary"]["scopes"] == 5
        assert len(body["alerts"]) == 5
        assert body["alerts"][0]["kind"] == "incident"
        assert body["alerts"][0]["action_label"] == "Open incident"
        assert body["copilot_prompt"]
        assert body["slack_preview"]
