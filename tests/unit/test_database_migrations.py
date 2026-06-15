"""Tests for the Alembic-backed database bootstrap."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, text

from app.core.migrations import upgrade_database
from app.core.database import build_engine


def test_initial_migration_can_adopt_an_existing_schema() -> None:
    """The first Alembic revision should not break old local databases."""

    repo_root = Path(__file__).resolve().parents[2]
    database_path = repo_root / ".tmp" / "unit" / "migration" / "nexusai-test.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        candidate = database_path.with_name(f"{database_path.name}{suffix}")
        if candidate.exists():
            candidate.unlink()

    database_url = f"sqlite+pysqlite:///{database_path}"

    engine = build_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE telemetry_signals (
                        id VARCHAR(36) PRIMARY KEY NOT NULL,
                        source_name VARCHAR(120) NOT NULL,
                        source_type VARCHAR(40) NOT NULL,
                        kind VARCHAR(40) NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        summary VARCHAR(255) NOT NULL,
                        description TEXT,
                        observed_at DATETIME NOT NULL,
                        received_at DATETIME NOT NULL,
                        batch_label VARCHAR(120),
                        service_name VARCHAR(120),
                        cluster_name VARCHAR(120),
                        workload_name VARCHAR(120),
                        namespace VARCHAR(120),
                        resource_type VARCHAR(80),
                        resource_name VARCHAR(120),
                        resource JSON NOT NULL,
                        attributes JSON NOT NULL,
                        payload JSON NOT NULL
                    )
                    """
                )
            )
    finally:
        engine.dispose()

    upgrade_database(database_url)

    verification_engine = build_engine(database_url)
    try:
        inspector = inspect(verification_engine)
        assert inspector.has_table("telemetry_signals")
        assert inspector.has_table("analysis_incidents")
        assert inspector.has_table("analysis_findings")
        assert inspector.has_table("analysis_evaluations")
        assert inspector.has_table("alembic_version")
        assert {"tenant_id", "actor_subject"}.issubset({column["name"] for column in inspector.get_columns("telemetry_signals")})
        assert {"tenant_id", "correlation_key", "state", "recommendations"}.issubset(
            {column["name"] for column in inspector.get_columns("analysis_incidents")}
        )
        assert {"tenant_id", "incident_id", "telemetry_signal_id", "category", "evidence"}.issubset(
            {column["name"] for column in inspector.get_columns("analysis_findings")}
        )
        assert {"tenant_id", "telemetry_signal_id", "finding_id", "outcome"}.issubset(
            {column["name"] for column in inspector.get_columns("analysis_evaluations")}
        )

        with verification_engine.connect() as connection:
            version_rows = list(connection.execute(text("SELECT version_num FROM alembic_version")))
        assert version_rows == [("0003_detection_core",)]
    finally:
        verification_engine.dispose()
