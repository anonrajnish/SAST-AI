"""Database engine and session management.

The engine is created lazily and cached so importing this module never opens a
connection (SQLAlchemy connects on first use). ``get_session`` is the FastAPI
dependency-injection entry point for a scoped session.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Return the process-wide SQLAlchemy engine (created on first call)."""

    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def _get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_session() -> Iterator[Session]:
    """Yield a database session and guarantee it is closed (DI dependency)."""

    session = _get_session_factory()()
    try:
        yield session
    finally:
        session.close()
