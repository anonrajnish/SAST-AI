"""Tests for the scan-job lifecycle (Slice 1)."""

from __future__ import annotations

import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.services.jobs import (
    InvalidScanJobTransitionError,
    ScanJob,
    ScanJobResult,
    ScanJobStatus,
    complete_scan_job,
    create_scan_job,
    fail_scan_job,
)
from app.services.scan import ScanConfig, ScanResult, ScanStatus
from app.services.upload import ArchiveScanResult, ExtractedRepository, scan_archive
from pydantic import ValidationError

_T0 = datetime(2026, 7, 18, 12, 0, 0, tzinfo=UTC)
_T1 = datetime(2026, 7, 18, 12, 0, 5, tzinfo=UTC)


# A minimal, self-contained ArchiveScanResult (no filesystem or real scan needed).
_ARCHIVE_RESULT = ArchiveScanResult(
    extraction=ExtractedRepository(
        root=Path("/tmp/sast-upload-xyz"), file_count=0, directory_count=0
    ),
    scan=ScanResult(
        status=ScanStatus.NO_SUPPORTED_LANGUAGES,
        detected_language_groups=frozenset(),
        resolved_language_groups=frozenset(),
        analyzer_runs=[],
        files_scanned=0,
        total_findings=0,
        findings=[],
    ),
)


@pytest.fixture
def archive_result() -> ArchiveScanResult:
    return _ARCHIVE_RESULT


def _pending() -> ScanJob:
    return create_scan_job(job_id="job-1", created_at=_T0)


# --- creation --------------------------------------------------------------------------


def test_create_scan_job_is_pending() -> None:
    job = _pending()

    assert job.job_id == "job-1"
    assert job.status is ScanJobStatus.PENDING
    assert job.created_at == _T0
    assert job.completed_at is None
    assert job.result is None
    assert job.error is None
    assert job.is_terminal is False


def test_create_scan_job_defaults_are_unique_and_utc() -> None:
    a = create_scan_job()
    b = create_scan_job()

    assert a.job_id != b.job_id  # fresh UUID each time
    assert a.created_at.tzinfo is not None  # timezone-aware (UTC)


# --- successful completion -------------------------------------------------------------


def test_complete_scan_job(archive_result: ArchiveScanResult) -> None:
    done = complete_scan_job(_pending(), archive_result, completed_at=_T1)

    assert done.status is ScanJobStatus.COMPLETED
    assert done.is_terminal is True
    assert done.completed_at == _T1
    assert done.result == ScanJobResult(scan=archive_result)
    assert done.error is None
    assert done.job_id == "job-1"
    assert done.created_at == _T0  # carried over


def test_complete_defaults_completed_at(archive_result: ArchiveScanResult) -> None:
    done = complete_scan_job(_pending(), archive_result)

    assert done.completed_at is not None
    assert done.completed_at.tzinfo is not None


def test_complete_from_running_is_allowed(archive_result: ArchiveScanResult) -> None:
    # RUNNING is reserved for a future async executor; completing from it must work.
    running = ScanJob(job_id="job-1", status=ScanJobStatus.RUNNING, created_at=_T0)

    done = complete_scan_job(running, archive_result, completed_at=_T1)

    assert done.status is ScanJobStatus.COMPLETED


def test_transition_returns_new_snapshot_leaving_original_unchanged(
    archive_result: ArchiveScanResult,
) -> None:
    pending = _pending()

    complete_scan_job(pending, archive_result, completed_at=_T1)

    assert pending.status is ScanJobStatus.PENDING  # original is untouched
    assert pending.result is None


# --- failed completion -----------------------------------------------------------------


def test_fail_scan_job() -> None:
    failed = fail_scan_job(_pending(), "boom: analyzer crashed", completed_at=_T1)

    assert failed.status is ScanJobStatus.FAILED
    assert failed.is_terminal is True
    assert failed.completed_at == _T1
    assert failed.error == "boom: analyzer crashed"
    assert failed.result is None


def test_fail_defaults_completed_at() -> None:
    failed = fail_scan_job(_pending(), "boom")

    assert failed.completed_at is not None


# --- invalid state transitions ---------------------------------------------------------


def test_completing_terminal_job_is_rejected(archive_result: ArchiveScanResult) -> None:
    done = complete_scan_job(_pending(), archive_result, completed_at=_T1)

    with pytest.raises(InvalidScanJobTransitionError) as exc_info:
        complete_scan_job(done, archive_result)
    assert exc_info.value.current_status is ScanJobStatus.COMPLETED
    assert exc_info.value.attempted == "complete"


def test_failing_terminal_job_is_rejected(archive_result: ArchiveScanResult) -> None:
    done = complete_scan_job(_pending(), archive_result, completed_at=_T1)

    with pytest.raises(InvalidScanJobTransitionError):
        fail_scan_job(done, "too late")


def test_transitioning_failed_job_is_rejected(
    archive_result: ArchiveScanResult,
) -> None:
    failed = fail_scan_job(_pending(), "boom", completed_at=_T1)

    with pytest.raises(InvalidScanJobTransitionError):
        complete_scan_job(failed, archive_result)
    with pytest.raises(InvalidScanJobTransitionError):
        fail_scan_job(failed, "again")


# --- model state-consistency invariants ------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": ScanJobStatus.COMPLETED},  # terminal without completed_at/result
        {"status": ScanJobStatus.FAILED},  # terminal without completed_at/error
        {"completed_at": _T1},  # non-terminal with completed_at
        {"status": ScanJobStatus.COMPLETED, "completed_at": _T1},  # completed w/o result
        {"error": "x"},  # non-failed carrying an error
        {"result": ScanJobResult(scan=_ARCHIVE_RESULT)},  # non-completed carrying a result
        {
            "status": ScanJobStatus.COMPLETED,
            "completed_at": _T1,
            "result": None,
            "error": "x",  # completed carrying an error
        },
    ],
)
def test_inconsistent_job_state_is_rejected(overrides: dict[str, Any]) -> None:
    kwargs: dict[str, Any] = {
        "job_id": "job-1",
        "status": ScanJobStatus.PENDING,
        "created_at": _T0,
    }
    kwargs.update(overrides)

    with pytest.raises(ValidationError):
        ScanJob(**kwargs)


def test_failed_job_requires_non_empty_error() -> None:
    with pytest.raises(ValidationError):
        ScanJob(
            job_id="job-1",
            status=ScanJobStatus.FAILED,
            created_at=_T0,
            completed_at=_T1,
            error="",
        )


# --- serialization & immutability ------------------------------------------------------


def test_scan_job_json_round_trips(archive_result: ArchiveScanResult) -> None:
    done = complete_scan_job(_pending(), archive_result, completed_at=_T1)

    dumped = done.model_dump(mode="json")
    assert dumped["job_id"] == "job-1"
    assert dumped["status"] == "completed"
    assert isinstance(dumped["created_at"], str)  # datetime -> ISO string
    assert dumped["result"]["scan"]["extraction"]["file_count"] == 0

    restored = ScanJob.model_validate(dumped)
    assert restored == done
    assert restored.created_at == _T0


def test_serialization_is_deterministic(archive_result: ArchiveScanResult) -> None:
    a = complete_scan_job(_pending(), archive_result, completed_at=_T1)
    b = complete_scan_job(_pending(), archive_result, completed_at=_T1)

    assert a.model_dump(mode="json") == b.model_dump(mode="json")


def test_scan_job_is_immutable(archive_result: ArchiveScanResult) -> None:
    job = _pending()
    result = ScanJobResult(scan=archive_result)

    with pytest.raises(ValidationError):
        job.status = ScanJobStatus.COMPLETED  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.scan = archive_result  # type: ignore[misc]


# --- integration: lifecycle around a real ArchiveScanResult ----------------------------


def test_lifecycle_around_real_scan_output(tmp_path: Path) -> None:
    archive = tmp_path / "repo.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("a.py", "import hashlib\nx = hashlib.md5(d)\n")

    scan_output = scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path)
    done = complete_scan_job(create_scan_job(), scan_output, completed_at=_T1)

    assert done.status is ScanJobStatus.COMPLETED
    assert done.result is not None
    assert done.result.scan is scan_output
    assert done.model_dump(mode="json")["result"]["scan"]["scan"]["total_findings"] >= 1
