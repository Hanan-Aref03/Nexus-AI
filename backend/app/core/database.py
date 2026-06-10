"""SQLAlchemy engine and connection helpers.

PR1 keeps persistence intentionally simple: a single normalized telemetry table
backed by PostgreSQL, with SQLite-friendly behavior for tests. Schema creation
now lives in Alembic so the database has one canonical versioned path.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def build_engine(database_url: str, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine with sane defaults for local development."""

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        echo=echo,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a session factory used by request-scoped dependencies."""

    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def ping_database(engine: Engine) -> dict[str, datetime | str]:
    """Run a lightweight readiness check against the active database."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "ready",
        "checked_at": datetime.now(timezone.utc),
    }


def close_engine(engine: Engine) -> None:
    """Dispose of pooled connections during application shutdown."""

    engine.dispose()
