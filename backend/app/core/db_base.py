"""Shared SQLAlchemy declarative base for the backend.

Every persistent domain imports this base so Alembic sees one canonical
metadata graph instead of one base per feature package.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared ORM base used by all backend domain models."""

