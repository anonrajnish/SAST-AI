"""Reusable FastAPI dependency-injection aliases.

Foundation-level wiring: typed dependencies for settings and database sessions, plus the
process-wide in-memory scan-job store that scan endpoints share as their single source of truth.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_session
from app.services.jobs import ScanJobStore

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]


@lru_cache
def get_scan_job_store() -> ScanJobStore:
    """Return the process-wide in-memory :class:`ScanJobStore` (a cached singleton).

    In-memory only (no persistence) — state lives for the process lifetime. Tests override this
    provider via ``app.dependency_overrides`` to inject a fresh, isolated store.
    """

    return ScanJobStore()


ScanJobStoreDep = Annotated[ScanJobStore, Depends(get_scan_job_store)]
