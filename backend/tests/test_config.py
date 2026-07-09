"""Tests for application configuration."""

from __future__ import annotations

import pytest
from app.config import Settings, get_settings


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()


def test_defaults_are_non_secret() -> None:
    settings = Settings()
    assert settings.app_env
    assert settings.database_url.startswith("postgresql")
    assert settings.redis_url.startswith("redis://")


def test_is_production_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    assert Settings().is_production is True
    monkeypatch.setenv("APP_ENV", "development")
    assert Settings().is_production is False
