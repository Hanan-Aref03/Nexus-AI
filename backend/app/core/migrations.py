"""Alembic helpers used by the backend startup path.

The application keeps a single canonical migration chain so the schema can be
reproduced locally, in Docker, and in future CI steps without relying on
``create_all`` shortcuts.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = BACKEND_ROOT / "alembic.ini"


def upgrade_database(database_url: str) -> None:
    """Upgrade the database to the latest Alembic revision.

    The initial migration is intentionally idempotent so existing local
    databases from the schema-on-startup era can be brought under Alembic
    control without dropping data.
    """

    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.set_main_option("prepend_sys_path", str(BACKEND_ROOT))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
