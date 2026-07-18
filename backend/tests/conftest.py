"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient bound to a freshly built app instance."""

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def write_file() -> Callable[[Path, str], None]:
    """Return a helper that writes ``text`` to ``path``, creating parent dirs.

    Shared by the deterministic-analyzer tests so each no longer defines its own
    ``_write`` helper.
    """

    def _write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    return _write
