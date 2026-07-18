"""Scan endpoints.

Write side (``POST /api/v1/scans``): runs one deterministic scan **synchronously** and returns the
final :class:`~app.services.jobs.ScanJob`. It only orchestrates existing components — creating a
job via the lifecycle functions, storing it in the shared :class:`~app.services.jobs.ScanJobStore`,
invoking the existing :func:`~app.services.upload.scan_archive`, then completing or failing the
job — and adds no extraction/scan/job logic of its own. A known upload or scan failure is a
recorded *outcome*: the job is marked ``FAILED`` and returned with HTTP 200, so the failure is
inspectable in the job's ``status``/``error``. Malformed requests are rejected by request
validation (HTTP 422) before any job is created.

Read side (``GET /api/v1/scans`` and ``GET /api/v1/scans/{job_id}``): returns jobs from the store
unchanged; a missing id raises :class:`~app.services.jobs.ScanJobNotFoundError`, mapped to HTTP 404
by the app-level exception handlers.

No multipart upload, background workers, persistence, auth, progress, cancellation, or export.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.dependencies import ScanJobStoreDep
from app.services.jobs import (
    ScanJob,
    complete_scan_job,
    create_scan_job,
    fail_scan_job,
)
from app.services.scan import ScanConfig, ScanError
from app.services.upload import UploadError, scan_archive

router = APIRouter(prefix="/scans", tags=["scans"])


class ScanRequest(BaseModel):
    """Request body for triggering a scan of an already-available archive.

    ``config`` reuses the existing :class:`~app.services.scan.ScanConfig` unchanged, so its
    validation (AUTO carries no groups, MANUAL requires at least one) applies to the request and
    an invalid combination is a 422 before any work happens. ``config`` defaults to AUTO.
    """

    model_config = ConfigDict(extra="forbid")

    archive_path: Path
    config: ScanConfig = Field(default_factory=ScanConfig.auto)


@router.post("", response_model=ScanJob)
def create_scan(request: ScanRequest, store: ScanJobStoreDep) -> ScanJob:
    """Create a job, run the scan synchronously, and return the completed/failed job."""

    job = create_scan_job()
    store.create(job)

    try:
        result = scan_archive(request.archive_path, request.config)
    except (UploadError, ScanError) as exc:
        failed = fail_scan_job(job, f"{type(exc).__name__}: {exc}")
        store.update(failed)
        return failed

    completed = complete_scan_job(job, result)
    store.update(completed)
    return completed


@router.get("", response_model=list[ScanJob])
def list_scans(store: ScanJobStoreDep) -> list[ScanJob]:
    """Return all scan jobs in the store's deterministic order (by created_at, then id)."""

    return list(store.list())


@router.get("/{job_id}", response_model=ScanJob)
def get_scan(job_id: str, store: ScanJobStoreDep) -> ScanJob:
    """Return one scan job; an unknown id raises ScanJobNotFoundError (mapped to HTTP 404)."""

    return store.get(job_id)
