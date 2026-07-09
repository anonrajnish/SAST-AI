"""Structured (JSON) logging foundation.

Establishes the base logging configuration required by AI_DEVELOPMENT_GUIDE §11:
structured output, redaction of sensitive fields, and support for bound context fields
(request/project/scan IDs). Per-request correlation middleware is intentionally NOT here
— that arrives with the first real endpoints (TASK-113).
"""

from __future__ import annotations

import logging
from typing import cast

import structlog
from structlog.stdlib import BoundLogger
from structlog.types import EventDict, Processor, WrappedLogger

# Keys whose values must never be emitted to logs (AI_DEVELOPMENT_GUIDE §11).
SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "secret_key",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "kek",
        "encrypted_key",
    }
)

_REDACTED = "***redacted***"


def _redact_sensitive(
    _logger: WrappedLogger, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Mask values whose key matches a known-sensitive name."""

    for key in list(event_dict.keys()):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = _REDACTED
    return event_dict


def configure_logging(*, level: str = "INFO", json_logs: bool = True) -> None:
    """Configure structlog + stdlib logging once, at application startup.

    Args:
        level: Root log level name (e.g. ``"INFO"``, ``"DEBUG"``).
        json_logs: Emit JSON (production) when True, human-readable console when False.
    """

    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    logging.basicConfig(format="%(message)s", level=numeric_level)

    renderer: Processor = (
        structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact_sensitive,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> BoundLogger:
    """Return a bound structured logger."""

    return cast(BoundLogger, structlog.get_logger(name))
