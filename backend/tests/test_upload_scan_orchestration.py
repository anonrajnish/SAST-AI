"""Tests for upload -> scan orchestration (Repository Upload Slice 2)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from app.config import Settings
from app.services.scan import (
    LanguageGroup,
    RepositoryError,
    ScanConfig,
    ScanExecutionError,
    ScanStatus,
)
from app.services.upload import (
    ArchiveScanResult,
    FileCountLimitError,
    PathTraversalError,
    UnsupportedArchiveError,
    scan_archive,
)
from pydantic import ValidationError

_MD5_PY = "import hashlib\nx = hashlib.md5(d)\n"  # weak crypto (python)
_SECRET_JS = 'const password = "S3cr3t-Example";\n'  # hardcoded secret (web)


def _make_zip(path: Path, files: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return path


# --- integration: real extract_zip + real scan_repository ------------------------------


def test_scan_archive_extracts_then_scans(tmp_path: Path) -> None:
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})

    result = scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)

    assert isinstance(result, ArchiveScanResult)
    assert result.extraction.file_count == 1
    assert result.extraction.root.is_dir()
    assert result.extraction.root.parent == tmp_path
    assert result.scan.status is ScanStatus.COMPLETED
    assert result.scan.total_findings >= 1
    assert any(f.location.file == "a.py" for f in result.scan.findings)


def test_scan_archive_empty_zip_reports_no_supported_languages(tmp_path: Path) -> None:
    archive = _make_zip(tmp_path / "empty.zip", {})

    result = scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)

    assert result.extraction.file_count == 0
    assert result.scan.status is ScanStatus.NO_SUPPORTED_LANGUAGES
    assert result.scan.findings == []


def test_scan_archive_honors_manual_language_scoping(tmp_path: Path) -> None:
    archive = _make_zip(tmp_path / "mixed.zip", {"a.py": _MD5_PY, "b.js": _SECRET_JS})

    result = scan_archive(
        archive, ScanConfig.manual([LanguageGroup.PYTHON]), workspace_dir=tmp_path
    )

    # Both languages are present, but MANUAL Python scopes findings to python files only.
    assert result.extraction.file_count == 2
    assert result.scan.detected_language_groups == frozenset(
        {LanguageGroup.PYTHON, LanguageGroup.WEB}
    )
    assert result.scan.resolved_language_groups == frozenset({LanguageGroup.PYTHON})
    assert {f.location.file for f in result.scan.findings} == {"a.py"}


def test_scan_archive_result_is_frozen_and_serializable(tmp_path: Path) -> None:
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})

    result = scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)

    dumped = result.model_dump(mode="json")
    assert set(dumped) == {"extraction", "scan"}
    assert dumped["extraction"]["file_count"] == 1
    assert dumped["scan"]["status"] == "completed"

    with pytest.raises(ValidationError):
        result.scan = result.scan  # type: ignore[misc]  # frozen
    with pytest.raises(ValidationError):
        ArchiveScanResult(
            extraction=result.extraction, scan=result.scan, extra=1  # type: ignore[call-arg]
        )


# --- error propagation (no wrapper exceptions) -----------------------------------------


def test_upload_error_propagates_and_scan_is_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A real Zip Slip archive: extraction rejects it and the scan stage must not run.
    archive = tmp_path / "slip.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(zipfile.ZipInfo("../evil.py"), "pwned\n")

    scanned = {"called": False}

    def _spy(*args: object, **kwargs: object) -> None:
        scanned["called"] = True

    monkeypatch.setattr("app.services.upload.orchestration.scan_repository", _spy)

    with pytest.raises(PathTraversalError):
        scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)
    assert scanned["called"] is False


def test_unsupported_archive_error_propagates_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = UnsupportedArchiveError("only .zip is accepted")

    def _raise(archive_path: Path, *, workspace_dir: Path | None = None) -> None:
        raise sentinel

    monkeypatch.setattr("app.services.upload.orchestration.extract_zip", _raise)

    with pytest.raises(UnsupportedArchiveError) as exc_info:
        scan_archive(tmp_path / "x.zip", ScanConfig.auto())
    assert exc_info.value is sentinel


def test_repository_error_propagates_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})
    sentinel = RepositoryError("repository root is not a directory")

    def _raise(root: Path, config: ScanConfig, **kwargs: object) -> None:
        raise sentinel

    monkeypatch.setattr("app.services.upload.orchestration.scan_repository", _raise)

    with pytest.raises(RepositoryError) as exc_info:
        scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)
    assert exc_info.value is sentinel


def test_scan_execution_error_propagates_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})
    sentinel = ScanExecutionError("weak-crypto-scanner", RuntimeError("boom"))

    def _raise(root: Path, config: ScanConfig, **kwargs: object) -> None:
        raise sentinel

    monkeypatch.setattr("app.services.upload.orchestration.scan_repository", _raise)

    with pytest.raises(ScanExecutionError) as exc_info:
        scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)
    assert exc_info.value is sentinel
    assert exc_info.value.detector_name == "weak-crypto-scanner"


def test_resource_limit_error_propagates_through_scan_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # scan_archive calls extract_zip without explicit limits, so the extractor sources them from
    # settings; a bomb/over-limit archive surfaces its typed error through the orchestration.
    monkeypatch.setattr(
        "app.services.upload.extractor.get_settings",
        lambda: Settings(extraction_max_file_count=1),
    )
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY, "b.py": "x = 1\n"})

    with pytest.raises(FileCountLimitError):
        scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)
