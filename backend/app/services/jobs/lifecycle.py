"""Scan-job lifecycle transitions (Slice 1).

Pure, deterministic, in-memory transition functions that each return a *new* immutable
:class:`~app.services.jobs.models.ScanJob` snapshot:

    create_scan_job()   -> PENDING
    complete_scan_job() -> COMPLETED   (attaches the ArchiveScanResult)
    fail_scan_job()     -> FAILED      (attaches an error message)

Jobs are in-memory only — no persistence, no async, no scheduling, no cancellation. Passing
``job_id`` / timestamps makes the result fully deterministic; the defaults use ``uuid4`` and the
current UTC time.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.services.upload import ArchiveScanResult

from .errors import InvalidScanJobTransitionError
from .models import ScanJob, ScanJobResult, ScanJobStatus


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def create_scan_job(
    *, job_id: str | None = None, created_at: datetime | None = None
) -> ScanJob:
    """Create a new job in the ``PENDING`` state.

    ``job_id`` defaults to a fresh UUID and ``created_at`` to the current UTC time; supply both
    for a fully deterministic result.
    """

    return ScanJob(
        job_id=job_id if job_id is not None else str(uuid4()),
        status=ScanJobStatus.PENDING,
        created_at=created_at if created_at is not None else _utcnow(),
    )


def complete_scan_job(
    job: ScanJob,
    result: ArchiveScanResult,
    *,
    completed_at: datetime | None = None,
) -> ScanJob:
    """Return a new ``COMPLETED`` snapshot of ``job`` carrying ``result``.

    Raises :class:`InvalidScanJobTransitionError` if ``job`` is already terminal.
    """

    _require_active(job, "complete")
    return ScanJob(
        job_id=job.job_id,
        status=ScanJobStatus.COMPLETED,
        created_at=job.created_at,
        completed_at=completed_at if completed_at is not None else _utcnow(),
        result=ScanJobResult(scan=result),
    )


def fail_scan_job(
    job: ScanJob,
    error: str,
    *,
    completed_at: datetime | None = None,
) -> ScanJob:
    """Return a new ``FAILED`` snapshot of ``job`` carrying the ``error`` message.

    Raises :class:`InvalidScanJobTransitionError` if ``job`` is already terminal.
    """

    _require_active(job, "fail")
    return ScanJob(
        job_id=job.job_id,
        status=ScanJobStatus.FAILED,
        created_at=job.created_at,
        completed_at=completed_at if completed_at is not None else _utcnow(),
        error=error,
    )


def _require_active(job: ScanJob, attempted: str) -> None:
    """Reject a transition from a terminal job (only PENDING/RUNNING jobs may transition)."""

    if job.is_terminal:
        raise InvalidScanJobTransitionError(job.status, attempted)
