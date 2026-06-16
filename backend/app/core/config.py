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
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    auth_signing_key: str = Field(default="dev-only-change-me")
    auth_token_issuer: str = "nexusai"
    auth_token_audience: str = "nexusai-web"
    vault_address: str | None = None
    vault_token: str | None = None
    vault_secret_mount: str = "secret"
    vault_secret_path: str = "nexusai/security"
    guardrails_enabled: bool = False
    ragas_enabled: bool = False
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    xai_api_key: str | None = None
    xai_model: str = "grok-4.3"
    copilot_timeout_seconds: float = 12.0
    copilot_max_context_items: int = 5
    otel_service_name: str = "nexusai-api"
    otel_console_exporter: bool = True
    slack_channel: str = "#nexusai-alerts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for normal application use."""

    return Settings()
