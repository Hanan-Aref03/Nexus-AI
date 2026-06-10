"""Add tenant isolation and audit columns for the security hardening slice."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.rls import build_tenant_rls_policy_sql


# revision identifiers, used by Alembic.
revision: str = "0002_security_hardening"
down_revision: Union[str, Sequence[str], None] = "0001_initial_telemetry_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_NAME = "telemetry_signals"


def upgrade() -> None:
    """Add tenant scoping columns and enable PostgreSQL row-level security."""

    op.add_column(
        TABLE_NAME,
        sa.Column(
            "tenant_id",
            sa.String(length=120),
            nullable=False,
            server_default=sa.text("'local-tenant'"),
        ),
    )
    op.add_column(TABLE_NAME, sa.Column("actor_subject", sa.String(length=120), nullable=True))
    op.create_index("ix_telemetry_signals_tenant_id", TABLE_NAME, ["tenant_id"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for statement in build_tenant_rls_policy_sql(TABLE_NAME):
            op.execute(statement)


def downgrade() -> None:
    """Remove the tenant isolation columns and the supporting index."""

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(f'DROP POLICY IF EXISTS telemetry_signals_tenant_isolation ON "{TABLE_NAME}"')
        op.execute(f'ALTER TABLE "{TABLE_NAME}" DISABLE ROW LEVEL SECURITY')

    op.drop_index("ix_telemetry_signals_tenant_id", table_name=TABLE_NAME)
    op.drop_column(TABLE_NAME, "actor_subject")
    op.drop_column(TABLE_NAME, "tenant_id")
