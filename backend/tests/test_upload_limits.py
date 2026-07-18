"""Tests for ZIP-bomb / resource-limit hardening (Repository Upload Slice 3)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from app.config import Settings
from app.services.upload import (
    ArchiveTooLargeError,
    CompressionRatioLimitError,
    ExtractedSizeLimitError,
    ExtractionLimits,
    FileCountLimitError,
    ResourceLimitError,
    extract_zip,
)
from app.services.upload.extractor import _copy_with_limit

# Generous baseline so each test can tighten exactly one bound in isolation.
_ROOMY = ExtractionLimits(
    max_archive_bytes=10 * 1024 * 1024,
    max_total_uncompressed_bytes=10 * 1024 * 1024,
    max_file_count=1000,
    max_compression_ratio=1000.0,
)


def _limits(**overrides: float) -> ExtractionLimits:
    return _ROOMY.model_copy(update=overrides)


def _stored_zip(path: Path, files: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return path


# --- valid archive within limits -------------------------------------------------------


def test_valid_archive_within_limits_succeeds(tmp_path: Path) -> None:
    archive = _stored_zip(tmp_path / "repo.zip", {"a.py": "x = 1\n", "b.py": "y = 2\n"})

    result = extract_zip(archive, workspace_dir=tmp_path, limits=_ROOMY)

    assert result.file_count == 2


# --- oversized archive -----------------------------------------------------------------


def test_oversized_archive_is_rejected(tmp_path: Path) -> None:
    archive = _stored_zip(tmp_path / "repo.zip", {"a.py": "x = 1\n"})

    with pytest.raises(ArchiveTooLargeError) as exc_info:
        extract_zip(archive, workspace_dir=tmp_path, limits=_limits(max_archive_bytes=10))
    assert exc_info.value.limit == 10
    assert exc_info.value.actual > 10
    # Rejected before opening: no extraction directory was created.
    assert list(tmp_path.iterdir()) == [archive]


# --- excessive file count --------------------------------------------------------------


def test_excessive_file_count_is_rejected(tmp_path: Path) -> None:
    archive = _stored_zip(
        tmp_path / "repo.zip", {"a.py": "1\n", "b.py": "2\n", "c.py": "3\n"}
    )

    with pytest.raises(FileCountLimitError) as exc_info:
        extract_zip(archive, workspace_dir=tmp_path, limits=_limits(max_file_count=2))
    assert exc_info.value.actual == 3
    assert exc_info.value.limit == 2


# --- excessive extracted size ----------------------------------------------------------


def test_excessive_extracted_size_is_rejected(tmp_path: Path) -> None:
    archive = _stored_zip(tmp_path / "repo.zip", {"big.txt": "A" * 100_000})

    with pytest.raises(ExtractedSizeLimitError):
        extract_zip(
            archive, workspace_dir=tmp_path, limits=_limits(max_total_uncompressed_bytes=1000)
        )


# --- excessive compression ratio (ZIP bomb simulation) ---------------------------------


def test_excessive_compression_ratio_is_rejected(tmp_path: Path) -> None:
    # 1 MiB of a single repeated byte deflates to ~1 KiB -> ratio ~1000:1.
    archive = tmp_path / "bomb.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bomb.txt", "A" * (1024 * 1024))

    with pytest.raises(CompressionRatioLimitError) as exc_info:
        extract_zip(archive, workspace_dir=tmp_path, limits=_limits(max_compression_ratio=50.0))
    assert exc_info.value.actual > 50.0
    assert list(tmp_path.iterdir()) == [archive]  # no partial extraction


def test_resource_limit_errors_are_upload_errors() -> None:
    # All limit violations share the ResourceLimitError base (an UploadError subclass), so they
    # propagate through scan_archive and map to a failed job at the REST layer.
    assert issubclass(ArchiveTooLargeError, ResourceLimitError)
    assert issubclass(FileCountLimitError, ResourceLimitError)
    assert issubclass(ExtractedSizeLimitError, ResourceLimitError)
    assert issubclass(CompressionRatioLimitError, ResourceLimitError)


# --- streaming cap (cannot be bypassed by a lying header) ------------------------------


def test_copy_with_limit_aborts_when_exceeded() -> None:
    src = io.BytesIO(b"x" * 1000)
    dst = io.BytesIO()

    with pytest.raises(ExtractedSizeLimitError):
        _copy_with_limit(src, dst, 0, 500)


def test_copy_with_limit_within_bound_returns_total() -> None:
    src = io.BytesIO(b"x" * 100)
    dst = io.BytesIO()

    assert _copy_with_limit(src, dst, 0, 500) == 100
    assert dst.getvalue() == b"x" * 100


# --- limits are sourced from the application configuration ------------------------------


def test_limits_default_to_application_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tiny = Settings(extraction_max_file_count=1)
    monkeypatch.setattr("app.services.upload.extractor.get_settings", lambda: tiny)
    archive = _stored_zip(tmp_path / "repo.zip", {"a.py": "1\n", "b.py": "2\n"})

    # No explicit limits -> the extractor sources them from the (patched) settings.
    with pytest.raises(FileCountLimitError):
        extract_zip(archive, workspace_dir=tmp_path)
