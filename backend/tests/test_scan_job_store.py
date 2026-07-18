"""Tests for the in-memory scan-job store (Slice 2)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.jobs import (
    DuplicateScanJobError,
    ScanJob,
    ScanJobNotFoundError,
    ScanJobResult,
    ScanJobStatus,
    ScanJobStore,
    complete_scan_job,
    create_scan_job,
    fail_scan_job,
)
from app.services.scan import ScanResult, ScanStatus
from app.services.upload import ArchiveScanResult, ExtractedRepository

_T0 = datetime(2026, 7, 18, 12, 0, 0, tzinfo=UTC)
_T1 = datetime(2026, 7, 18, 12, 0, 5, tzinfo=UTC)

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


def _job(job_id: str, *, created_at: datetime = _T0) -> ScanJob:
    return create_scan_job(job_id=job_id, created_at=created_at)


# --- create / get ----------------------------------------------------------------------


def test_create_and_get() -> None:
    store = ScanJobStore()
    job = _job("job-1")

    store.create(job)

    assert store.get("job-1") is job  # stored unchanged, returned by reference


def test_create_rejects_duplicate_job_id() -> None:
    store = ScanJobStore()
    store.create(_job("job-1"))

    with pytest.raises(DuplicateScanJobError) as exc_info:
        store.create(_job("job-1"))
    assert exc_info.value.job_id == "job-1"


def test_get_missing_job_raises() -> None:
    store = ScanJobStore()

    with pytest.raises(ScanJobNotFoundError) as exc_info:
        store.get("nope")
    assert exc_info.value.job_id == "nope"


# --- update ----------------------------------------------------------------------------


def test_update_replaces_snapshot() -> None:
    store = ScanJobStore()
    store.create(_job("job-1"))

    failed = fail_scan_job(store.get("job-1"), "boom", completed_at=_T1)
    store.update(failed)

    fetched = store.get("job-1")
    assert fetched is failed
    assert fetched.status is ScanJobStatus.FAILED
    assert fetched.error == "boom"


def test_update_missing_job_raises() -> None:
    store = ScanJobStore()

    with pytest.raises(ScanJobNotFoundError) as exc_info:
        store.update(_job("ghost"))
    assert exc_info.value.job_id == "ghost"


def test_update_does_not_create() -> None:
    store = ScanJobStore()

    with pytest.raises(ScanJobNotFoundError):
        store.update(_job("job-1"))
    with pytest.raises(ScanJobNotFoundError):
        store.get("job-1")  # nothing was inserted by the failed update


# --- list ------------------------------------------------------------------------------


def test_list_empty() -> None:
    assert ScanJobStore().list() == ()


def test_list_is_ordered_by_created_at_then_id() -> None:
    store = ScanJobStore()
    # Insert out of chronological order; list() must return a canonical order.
    store.create(_job("b", created_at=_T1))
    store.create(_job("a", created_at=_T0))
    store.create(_job("c", created_at=_T1))

    assert [j.job_id for j in store.list()] == ["a", "b", "c"]


def test_list_returns_immutable_snapshot() -> None:
    store = ScanJobStore()
    store.create(_job("job-1"))

    listing = store.list()
    store.create(_job("job-2"))

    assert isinstance(listing, tuple)
    assert [j.job_id for j in listing] == ["job-1"]  # earlier snapshot unaffected


# --- serialization compatibility -------------------------------------------------------


def test_stored_jobs_remain_serializable() -> None:
    store = ScanJobStore()
    store.create(_job("job-1"))
    done = complete_scan_job(store.get("job-1"), _ARCHIVE_RESULT, completed_at=_T1)
    store.update(done)

    dumped = store.get("job-1").model_dump(mode="json")
    assert dumped["status"] == "completed"
    assert dumped["result"]["scan"]["extraction"]["file_count"] == 0
    assert ScanJob.model_validate(dumped) == done

    # Every job from list() round-trips through JSON too.
    for job in store.list():
        assert ScanJob.model_validate(job.model_dump(mode="json")) == job


# --- integration: store as source of truth across a lifecycle --------------------------


def test_store_tracks_full_lifecycle() -> None:
    store = ScanJobStore()
    pending = create_scan_job(job_id="job-1", created_at=_T0)
    store.create(pending)
    assert store.get("job-1").status is ScanJobStatus.PENDING

    store.update(complete_scan_job(pending, _ARCHIVE_RESULT, completed_at=_T1))

    final = store.get("job-1")
    assert final.status is ScanJobStatus.COMPLETED
    assert final.result == ScanJobResult(scan=_ARCHIVE_RESULT)


# --- thread safety ---------------------------------------------------------------------


def test_concurrent_creates_are_all_recorded() -> None:
    store = ScanJobStore()
    n = 500

    def worker(i: int) -> None:
        store.create(_job(f"job-{i}"))

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(worker, range(n)))

    listing = store.list()
    assert len(listing) == n
    assert {j.job_id for j in listing} == {f"job-{i}" for i in range(n)}


def test_concurrent_updates_do_not_corrupt_store() -> None:
    store = ScanJobStore()
    store.create(_job("job-1"))

    def worker(i: int) -> None:
        completed_at = datetime(2026, 7, 18, 12, 0, i % 60, tzinfo=UTC)
        store.update(fail_scan_job(_job("job-1"), f"err-{i}", completed_at=completed_at))

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(worker, range(500)))

    listing = store.list()
    assert len(listing) == 1  # still exactly one job, no duplication/corruption
    assert listing[0].status is ScanJobStatus.FAILED
