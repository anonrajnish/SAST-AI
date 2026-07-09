"""Application configuration loaded from environment variables (Pydantic v2).

Only the settings the engineering foundation actually uses are declared here (app
metadata, logging, database, redis). Additional keys present in the environment or
``.env`` (e.g. scan limits, KEK path) are ignored for now and will be declared by the
feature tasks that consume them. No secrets or credentials are hardcoded.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings sourced from the environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", description="development | uat | production")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Datastores (override via environment / secret store; no real credentials here)
    database_url: str = Field(
        default="postgresql+psycopg://postgres@localhost:5432/sastdb",
        description="SQLAlchemy DSN; password injected via env/secret store.",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance (dependency-injection friendly)."""

    return Settings()
