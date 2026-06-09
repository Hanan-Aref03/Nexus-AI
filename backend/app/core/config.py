"""Application settings.

The defaults intentionally favor local development so PR1 can run without any
paid services or external cloud dependencies.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    project_name: str = "NexusAI"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = Field(
        default="postgresql+psycopg2://nexusai:nexusai@localhost:5432/nexusai"
    )
    database_echo: bool = False
    otel_service_name: str = "nexusai-api"
    otel_console_exporter: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for normal application use."""

    return Settings()

