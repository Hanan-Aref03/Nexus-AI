"""Integration smoke test for the Phase 2 detection core."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.config import Settings
from app.factory import create_app
from app.domains.telemetry.sample_data import build_demo_batch


def build_test_settings() -> Settings:
    """Build a file-backed SQLite configuration for an isolated Phase 2 test."""

    repo_root = Path(__file__).resolve().parents[2]
    database_path = repo_root / ".tmp" / "integration" / "phase2-detection-core.db"
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


def test_detection_core_flow_detects_correlated_incidents() -> None:
    """Smoke test telemetry ingestion, detection, incident control, and health."""

    app = create_app(build_test_settings())

    with TestClient(app) as client:
        token = create_access_token(
            app.state.runtime_secrets,
            subject="tester-analysis",
            tenant_id="payments",
            roles=("telemetry:read", "telemetry:write", "analysis:read", "analysis:write"),
            issuer=app.state.settings.auth_token_issuer,
            audience=app.state.settings.auth_token_audience,
        )
        headers = {"Authorization": f"Bearer {token}"}

        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "ok"

        ready_response = client.get("/ready")
        assert ready_response.status_code == 200
        assert ready_response.json()["status"] == "ready"

        ingest_response = client.post(
            "/api/v1/telemetry/ingest",
            json=build_demo_batch().model_dump(mode="json"),
            headers=headers,
        )
        assert ingest_response.status_code == 201

        first_run = client.post("/api/v1/analysis/run?limit=50", headers=headers)
        assert first_run.status_code == 200
        first_run_body = first_run.json()
        assert first_run_body["processed_signals"] == 2
        assert first_run_body["created_findings"] == 2
        assert first_run_body["created_incidents"] == 1
        assert first_run_body["updated_incidents"] == 0
        assert len(first_run_body["health_scores"]) == 4
        assert {item["scope_name"] for item in first_run_body["health_scores"]} == {
            "checkout-api",
            "checkout-deployment",
            "redis-cache",
            "redis-statefulset",
        }
        assert all(item["status"] != "healthy" for item in first_run_body["health_scores"])

        second_run = client.post("/api/v1/analysis/run?limit=50", headers=headers)
        assert second_run.status_code == 200
        second_run_body = second_run.json()
        assert second_run_body == {
            "processed_signals": 0,
            "created_findings": 0,
            "created_incidents": 0,
            "updated_incidents": 0,
            "health_scores": first_run_body["health_scores"],
        }

        findings_response = client.get("/api/v1/analysis/findings?limit=20", headers=headers)
        assert findings_response.status_code == 200
        findings = findings_response.json()
        assert len(findings) == 2
        assert {item["category"] for item in findings} == {"reliability", "capacity"}
        assert len({item["correlation_key"] for item in findings}) == 1

        incidents_response = client.get("/api/v1/analysis/incidents?limit=20", headers=headers)
        assert incidents_response.status_code == 200
        incidents = incidents_response.json()
        assert len(incidents) == 1
        incident_id = incidents[0]["id"]
        assert incidents[0]["state"] == "open"
        assert incidents[0]["evidence_count"] == 2
        assert incidents[0]["finding_count"] == 2
        assert len(incidents[0]["evidence"]) == 2

        incident_detail = client.get(f"/api/v1/analysis/incidents/{incident_id}", headers=headers)
        assert incident_detail.status_code == 200
        assert len(incident_detail.json()["evidence"]) == 2

        investigating_response = client.patch(
            f"/api/v1/analysis/incidents/{incident_id}",
            json={"state": "investigating"},
            headers=headers,
        )
        assert investigating_response.status_code == 200
        assert investigating_response.json()["state"] == "investigating"

        resolved_response = client.patch(
            f"/api/v1/analysis/incidents/{incident_id}",
            json={"state": "resolved"},
            headers=headers,
        )
        assert resolved_response.status_code == 200
        assert resolved_response.json()["state"] == "resolved"
        assert resolved_response.json()["resolved_at"] is not None

        health_scores_response = client.get("/api/v1/analysis/health-scores?limit=20", headers=headers)
        assert health_scores_response.status_code == 200
        assert health_scores_response.json() == []

