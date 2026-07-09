"""Tests for the database foundation (no live connection required)."""

from __future__ import annotations

from app.db.base import Base
from app.db.session import get_engine, get_session
from sqlalchemy import Engine


def test_metadata_is_available() -> None:
    assert Base.metadata is not None


def test_engine_is_cached() -> None:
    assert isinstance(get_engine(), Engine)
    assert get_engine() is get_engine()


def test_get_session_closes() -> None:
    generator = get_session()
    session = next(generator)
    assert session is not None
    generator.close()  # triggers the finally-block close
