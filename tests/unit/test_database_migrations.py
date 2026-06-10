"""Tests for the Alembic-backed database bootstrap."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, text

from app.core.database import build_engine
from app.core.migrations import upgrade_database
from app.domains.telemetry.models import Base


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
        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()

    upgrade_database(database_url)

    verification_engine = build_engine(database_url)
    try:
        inspector = inspect(verification_engine)
        assert inspector.has_table("telemetry_signals")
        assert inspector.has_table("alembic_version")

        with verification_engine.connect() as connection:
            version_rows = list(connection.execute(text("SELECT version_num FROM alembic_version")))
        assert version_rows == [("0001_initial_telemetry_schema",)]
    finally:
        verification_engine.dispose()
