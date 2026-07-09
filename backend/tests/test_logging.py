"""Tests for the structured logging foundation."""

from __future__ import annotations

from app.core.logging import _redact_sensitive, configure_logging, get_logger


def test_configure_logging_json_and_console() -> None:
    configure_logging(level="INFO", json_logs=True)
    configure_logging(level="DEBUG", json_logs=False)
    assert get_logger("test") is not None


def test_invalid_level_falls_back() -> None:
    # Should not raise even with a bogus level name.
    configure_logging(level="NOT_A_LEVEL")


def test_sensitive_values_are_redacted() -> None:
    event = {"password": "hunter2", "api_key": "sk-123", "user": "bob"}
    redacted = _redact_sensitive(None, "info", event)  # type: ignore[arg-type]
    assert redacted["password"] == "***redacted***"
    assert redacted["api_key"] == "***redacted***"
    assert redacted["user"] == "bob"
