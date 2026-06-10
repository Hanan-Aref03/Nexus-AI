"""Create the initial telemetry storage schema.

This migration is intentionally idempotent so existing databases created by the
earlier schema-on-startup bootstrap can move under Alembic without data loss.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.engine import Connection


# revision identifiers, used by Alembic.
revision: str = "0001_initial_telemetry_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_NAME = "telemetry_signals"


def _existing_index_names(connection: Connection) -> set[str]:
    """Return the current index names for the telemetry table."""

    inspector = inspect(connection)
    if not inspector.has_table(TABLE_NAME):
        return set()
    return {index["name"] for index in inspector.get_indexes(TABLE_NAME)}


def upgrade() -> None:
    """Create the normalized telemetry table and its lookup indexes."""

    connection = op.get_bind()
    existing_indexes = _existing_index_names(connection)

    if not inspect(connection).has_table(TABLE_NAME):
        op.create_table(
            TABLE_NAME,
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column("source_name", sa.String(length=120), nullable=False),
            sa.Column("source_type", sa.String(length=40), nullable=False),
            sa.Column("kind", sa.String(length=40), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False),
            sa.Column("summary", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "received_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("batch_label", sa.String(length=120), nullable=True),
            sa.Column("service_name", sa.String(length=120), nullable=True),
            sa.Column("cluster_name", sa.String(length=120), nullable=True),
            sa.Column("workload_name", sa.String(length=120), nullable=True),
            sa.Column("namespace", sa.String(length=120), nullable=True),
            sa.Column("resource_type", sa.String(length=80), nullable=True),
            sa.Column("resource_name", sa.String(length=120), nullable=True),
            sa.Column("resource", sa.JSON(), nullable=False),
            sa.Column("attributes", sa.JSON(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
        )

    index_definitions = [
        ("ix_telemetry_signals_source_type", ["source_type"]),
        ("ix_telemetry_signals_kind", ["kind"]),
        ("ix_telemetry_signals_service_name", ["service_name"]),
        ("ix_telemetry_signals_observed_at", ["observed_at"]),
    ]
    for index_name, columns in index_definitions:
        if index_name not in existing_indexes:
            op.create_index(index_name, TABLE_NAME, columns)


def downgrade() -> None:
    """Remove the initial telemetry storage schema."""

    op.drop_index("ix_telemetry_signals_observed_at", table_name=TABLE_NAME)
    op.drop_index("ix_telemetry_signals_service_name", table_name=TABLE_NAME)
    op.drop_index("ix_telemetry_signals_kind", table_name=TABLE_NAME)
    op.drop_index("ix_telemetry_signals_source_type", table_name=TABLE_NAME)
    op.drop_table(TABLE_NAME)
