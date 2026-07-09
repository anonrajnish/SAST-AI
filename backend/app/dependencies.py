"""Reusable FastAPI dependency-injection aliases.

Foundation-level wiring: typed dependencies for settings and database sessions that
feature routers will reuse. No business dependencies are defined here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_session

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]
