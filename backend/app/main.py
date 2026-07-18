"""FastAPI application factory.

Wires configuration, structured logging, and the API router. No business routers are
mounted — only health/liveness/readiness exist in the engineering foundation.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.meta import APP_NAME, APP_VERSION


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    settings = get_settings()
    configure_logging(level=settings.log_level, json_logs=not settings.debug)

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        debug=settings.debug,
    )
    app.include_router(api_router, prefix="/api/v1")

    get_logger(__name__).info("application_configured", app_env=settings.app_env)
    return app


app = create_app()
