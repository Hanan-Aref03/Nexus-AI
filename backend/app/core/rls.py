"""Tenant scoping helpers for PostgreSQL row-level security."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import SecurityPrincipal


def apply_tenant_context(session: Session, principal: SecurityPrincipal) -> None:
    """Bind the active tenant to the current SQLAlchemy session.

    PostgreSQL row-level security reads these session-local values during query
    execution. SQLite ignores the helper, which keeps local tests portable.
    """

    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return

    session.execute(
        text(
            """
            SELECT
                set_config('app.current_tenant', :tenant_id, true),
                set_config('app.current_subject', :subject, true),
                set_config('app.current_roles', :roles, true)
            """
        ),
        {
            "tenant_id": principal.tenant_id,
            "subject": principal.subject,
            "roles": ",".join(principal.roles),
        },
    )


def build_tenant_rls_policy_sql(table_name: str, tenant_column: str = "tenant_id") -> list[str]:
    """Return the SQL statements used by the migration for PostgreSQL RLS."""

    policy_name = f"{table_name}_tenant_isolation"
    qualified_column = f'"{tenant_column}"'
    qualified_table = f'"{table_name}"'

    return [
        f"ALTER TABLE {qualified_table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {qualified_table} FORCE ROW LEVEL SECURITY",
        (
            f"CREATE POLICY {policy_name} ON {qualified_table} "
            f"USING ({qualified_column} = current_setting('app.current_tenant', true)) "
            f"WITH CHECK ({qualified_column} = current_setting('app.current_tenant', true))"
        ),
    ]
