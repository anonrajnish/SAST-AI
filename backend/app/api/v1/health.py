"""Health, liveness, and readiness endpoints.

These are the only endpoints in the engineering foundation. Liveness reports process
health; readiness verifies downstream dependencies (currently the database — the Redis
check is added with TASK-120 when the Redis client is introduced).
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.db.session import get_engine
from app.dependencies import SettingsDep

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


@router.get("")
def health(settings: SettingsDep) -> dict[str, str]:
    """Basic health check."""

    return {"status": "ok", "app_env": settings.app_env}


@router.get("/live")
def live() -> dict[str, str]:
    """Liveness probe: the process is running."""

    return {"status": "alive"}


@router.get("/ready")
def ready(response: Response) -> dict[str, str]:
    """Readiness probe: verify the database is reachable.

    Returns HTTP 503 with ``status: not_ready`` when a dependency is unavailable so
    orchestrators do not route traffic to an unready instance.
    """

    database_ok = True
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        database_ok = False
        # Do not log the exception detail — DSNs can carry connection metadata (§11).
        logger.warning("readiness_check_failed", check="database")

    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if database_ok else "not_ready",
        "database": "ok" if database_ok else "unavailable",
    }
