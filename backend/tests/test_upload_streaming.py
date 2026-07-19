"""Tests for the streaming upload helper (Multipart Upload slice)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from app.services.upload import ArchiveTooLargeError, sanitize_upload_filename, stream_zip_to_temp


def test_stream_within_cap_writes_all_bytes(tmp_path: Path) -> None:
    payload = b"PK\x03\x04 pretend zip bytes" * 10
    source = io.BytesIO(payload)

    path = stream_zip_to_temp(source, max_bytes=10_000, directory=tmp_path)

    assert path.parent == tmp_path
    assert path.suffix == ".zip"
    assert path.read_bytes() == payload
    path.unlink()


def test_stream_over_cap_raises_and_cleans_up(tmp_path: Path) -> None:
    source = io.BytesIO(b"x" * 5000)

    with pytest.raises(ArchiveTooLargeError) as exc_info:
        stream_zip_to_temp(source, max_bytes=1000, directory=tmp_path)

    assert exc_info.value.limit == 1000
    assert exc_info.value.actual > 1000
    # The partial temp file was removed on failure — nothing left behind.
    assert list(tmp_path.iterdir()) == []


def test_stream_error_cleans_up(tmp_path: Path) -> None:
    class _Boom:
        def read(self, size: int = -1) -> bytes:
            raise OSError("connection reset")  # simulates a client disconnect mid-upload

    with pytest.raises(OSError, match="connection reset"):
        stream_zip_to_temp(_Boom(), max_bytes=10_000, directory=tmp_path)  # type: ignore[arg-type]

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("repo.zip", "repo.zip"),
        ("../../etc/passwd", "passwd"),
        ("/abs/path/evil.zip", "evil.zip"),
        ("we ird!$name.zip", "we_ird__name.zip"),
        ("", "upload.zip"),
        (None, "upload.zip"),
    ],
)
def test_sanitize_upload_filename(raw: str | None, expected: str) -> None:
    assert sanitize_upload_filename(raw) == expected


def test_sanitize_upload_filename_truncates_long_names() -> None:
    result = sanitize_upload_filename("a" * 500 + ".zip")

    assert len(result) == 128
