"""FastAPI dependencies for app state access."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from app.domains.telemetry.adapters.base import AdapterRegistry


def get_session(request: Request) -> Iterator[Session]:
    """Yield a request-scoped SQLAlchemy session."""

    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_adapter_registry(request: Request) -> AdapterRegistry:
    """Expose the active source-adapter registry to request handlers."""

    return request.app.state.adapter_registry

