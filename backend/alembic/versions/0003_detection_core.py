"""Create the Phase 2 detection-core tables.

The migration keeps the analysis layer tenant-aware and idempotent so local
databases can be upgraded from any earlier phase without data loss.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

from app.core.rls import build_tenant_rls_policy_sql


# revision identifiers, used by Alembic.
revision: str = "0003_detection_core"
down_revision: Union[str, Sequence[str], None] = "0002_security_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INCIDENTS_TABLE = "analysis_incidents"
FINDINGS_TABLE = "analysis_findings"
EVALUATIONS_TABLE = "analysis_evaluations"


def _existing_index_names(connection: Connection, table_name: str) -> set[str]:
    """Return the current index names for a specific table."""

    inspector = inspect(connection)
    if not inspector.has_table(table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _apply_rls(table_name: str) -> None:
    """Enable PostgreSQL row-level security for a detection table."""

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for statement in build_tenant_rls_policy_sql(table_name):
            op.execute(statement)


def _create_table_if_missing(table_name: str, columns: list[sa.Column]) -> None:
    """Create a table only when it does not already exist."""

    connection = op.get_bind()
    if not inspect(connection).has_table(table_name):
        op.create_table(table_name, *columns)


def upgrade() -> None:
    """Create the incident, finding, and evaluation tables."""

    _create_table_if_missing(
        INCIDENTS_TABLE,
        [
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column(
                "tenant_id",
                sa.String(length=120),
                nullable=False,
                server_default=sa.text("'local-tenant'"),
            ),
            sa.Column("correlation_key", sa.String(length=255), nullable=False),
            sa.Column("scope_kind", sa.String(length=40), nullable=False),
            sa.Column("scope_name", sa.String(length=120), nullable=False),
            sa.Column("state", sa.String(length=20), nullable=False, server_default=sa.text("'open'")),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("probable_cause", sa.String(length=255), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("evidence_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("finding_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("service_name", sa.String(length=120), nullable=True),
            sa.Column("workload_name", sa.String(length=120), nullable=True),
            sa.Column("cluster_name", sa.String(length=120), nullable=True),
            sa.Column("namespace", sa.String(length=120), nullable=True),
            sa.Column("recommendations", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        ],
    )

    _create_table_if_missing(
        FINDINGS_TABLE,
        [
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column(
                "tenant_id",
                sa.String(length=120),
                nullable=False,
                server_default=sa.text("'local-tenant'"),
            ),
            sa.Column(
                "incident_id",
                sa.String(length=36),
                sa.ForeignKey(f"{INCIDENTS_TABLE}.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "telemetry_signal_id",
                sa.String(length=36),
                sa.ForeignKey("telemetry_signals.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("correlation_key", sa.String(length=255), nullable=False),
            sa.Column("source_name", sa.String(length=120), nullable=False),
            sa.Column("source_type", sa.String(length=40), nullable=False),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("batch_label", sa.String(length=120), nullable=True),
            sa.Column("category", sa.String(length=40), nullable=False),
            sa.Column("kind", sa.String(length=40), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("recommendations", sa.JSON(), nullable=False),
            sa.Column("service_name", sa.String(length=120), nullable=True),
            sa.Column("workload_name", sa.String(length=120), nullable=True),
            sa.Column("cluster_name", sa.String(length=120), nullable=True),
            sa.Column("namespace", sa.String(length=120), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        ],
    )

    _create_table_if_missing(
        EVALUATIONS_TABLE,
        [
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column(
                "tenant_id",
                sa.String(length=120),
                nullable=False,
                server_default=sa.text("'local-tenant'"),
            ),
            sa.Column(
                "telemetry_signal_id",
                sa.String(length=36),
                sa.ForeignKey("telemetry_signals.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("correlation_key", sa.String(length=255), nullable=False),
            sa.Column("outcome", sa.String(length=20), nullable=False),
            sa.Column("category", sa.String(length=40), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column(
                "finding_id",
                sa.String(length=36),
                sa.ForeignKey(f"{FINDINGS_TABLE}.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "evaluated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        ],
    )

    connection = op.get_bind()
    for table_name, index_definitions in {
        INCIDENTS_TABLE: [
            ("ix_analysis_incidents_tenant_id", ["tenant_id"]),
            ("ix_analysis_incidents_state", ["state"]),
            ("ix_analysis_incidents_correlation_key", ["correlation_key"]),
            ("ix_analysis_incidents_scope_kind", ["scope_kind"]),
            ("ix_analysis_incidents_scope_name", ["scope_name"]),
            ("ix_analysis_incidents_updated_at", ["updated_at"]),
        ],
        FINDINGS_TABLE: [
            ("ix_analysis_findings_tenant_id", ["tenant_id"]),
            ("ix_analysis_findings_incident_id", ["incident_id"]),
            ("ix_analysis_findings_telemetry_signal_id", ["telemetry_signal_id"]),
            ("ix_analysis_findings_category", ["category"]),
            ("ix_analysis_findings_severity", ["severity"]),
            ("ix_analysis_findings_service_name", ["service_name"]),
            ("ix_analysis_findings_workload_name", ["workload_name"]),
            ("ix_analysis_findings_created_at", ["created_at"]),
        ],
        EVALUATIONS_TABLE: [
            ("ix_analysis_evaluations_tenant_id", ["tenant_id"]),
            ("ix_analysis_evaluations_telemetry_signal_id", ["telemetry_signal_id"]),
            ("ix_analysis_evaluations_outcome", ["outcome"]),
            ("ix_analysis_evaluations_category", ["category"]),
            ("ix_analysis_evaluations_evaluated_at", ["evaluated_at"]),
        ],
    }.items():
        existing_indexes = _existing_index_names(connection, table_name)
        for index_name, columns in index_definitions:
            if index_name not in existing_indexes:
                op.create_index(index_name, table_name, columns, unique=index_name.endswith("telemetry_signal_id"))

    for table_name in (INCIDENTS_TABLE, FINDINGS_TABLE, EVALUATIONS_TABLE):
        _apply_rls(table_name)


def downgrade() -> None:
    """Drop the detection-core tables."""

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table_name in (EVALUATIONS_TABLE, FINDINGS_TABLE, INCIDENTS_TABLE):
            op.execute(f'DROP POLICY IF EXISTS {table_name}_tenant_isolation ON "{table_name}"')
            op.execute(f'ALTER TABLE "{table_name}" DISABLE ROW LEVEL SECURITY')

    op.drop_table(EVALUATIONS_TABLE)
    op.drop_table(FINDINGS_TABLE)
    op.drop_table(INCIDENTS_TABLE)

