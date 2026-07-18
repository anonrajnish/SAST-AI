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

    # Upload extraction resource limits (ZIP-bomb / resource-exhaustion hardening).
    # Override via env (e.g. EXTRACTION_MAX_ARCHIVE_BYTES). Consumed by the upload extractor.
    extraction_max_archive_bytes: int = Field(
        default=100 * 1024 * 1024, gt=0, description="Max on-disk .zip size (bytes)."
    )
    extraction_max_total_uncompressed_bytes: int = Field(
        default=1024 * 1024 * 1024, gt=0, description="Max total extracted size (bytes)."
    )
    extraction_max_file_count: int = Field(
        default=10_000, gt=0, description="Max number of archive member entries."
    )
    extraction_max_compression_ratio: float = Field(
        default=100.0, gt=0, description="Max total uncompressed / compressed ratio."
    )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance (dependency-injection friendly)."""

    return Settings()
