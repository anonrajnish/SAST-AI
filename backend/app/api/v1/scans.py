"""Scan endpoints.

Write side (``POST /api/v1/scans``): accepts a **multipart upload** of a repository ZIP plus the
target-language selection, runs one deterministic scan **synchronously**, and returns the final
:class:`~app.services.jobs.ScanJob`. The endpoint is orchestration-only — it streams the upload to
a server-chosen temp file (via the upload package), then reuses the existing components (job
lifecycle, :func:`~app.services.upload.scan_archive`, :class:`~app.services.jobs.ScanJobStore`).

Request-level failures are rejected before any job is created: a missing file or an invalid
:class:`~app.services.scan.ScanConfig` combination is **422**, and an upload exceeding the archive
size limit is **413**. A known upload/scan failure of a validly-received archive is a recorded
*outcome*: the job is marked ``FAILED`` and returned with HTTP 200. The uploaded temp file is
deleted on **every** exit path (success, failure, oversize, or client disconnect) via ``finally``.

Read side (``GET /api/v1/scans`` and ``GET /api/v1/scans/{job_id}``): returns jobs from the store
unchanged; a missing id raises :class:`~app.services.jobs.ScanJobNotFoundError`, mapped to HTTP 404.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from app.core.logging import get_logger
from app.dependencies import ScanJobStoreDep, SettingsDep
from app.services.jobs import (
    ScanJob,
    complete_scan_job,
    create_scan_job,
    fail_scan_job,
)
from app.services.scan import LanguageGroup, ScanConfig, ScanError, TargetMode
from app.services.upload import (
    ArchiveTooLargeError,
    UploadError,
    sanitize_upload_filename,
    scan_archive,
    stream_zip_to_temp,
)

router = APIRouter(prefix="/scans", tags=["scans"])
logger = get_logger(__name__)


def scan_config_from_form(
    mode: Annotated[TargetMode, Form()] = TargetMode.AUTO,
    groups: Annotated[list[LanguageGroup] | None, Form()] = None,
) -> ScanConfig:
    """Reconstruct a :class:`ScanConfig` from multipart form fields.

    Transport-agnostic: it only constructs the config and lets ``ScanConfig`` validation raise
    ``ValidationError`` (AUTO carries no groups; MANUAL requires at least one). The REST layer's
    exception handler translates that into HTTP 422.
    """

    return ScanConfig(mode=mode, groups=frozenset(groups or []))


@router.post("", response_model=ScanJob)
def create_scan(
    settings: SettingsDep,
    store: ScanJobStoreDep,
    config: Annotated[ScanConfig, Depends(scan_config_from_form)],
    file: Annotated[UploadFile, File()],
    content_length: Annotated[int | None, Header()] = None,
) -> ScanJob:
    """Stream the uploaded ZIP, scan it synchronously, and return the completed/failed job."""

    max_bytes = settings.extraction_max_archive_bytes
    if content_length is not None and content_length > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"upload exceeds the maximum archive size of {max_bytes} bytes",
        )

    try:
        upload_path = stream_zip_to_temp(file.file, max_bytes=max_bytes)
    except ArchiveTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc

    # From here the temp upload file is deleted on every exit path — success, scan failure,
    # an unexpected error, or a client disconnect — via this outer ``finally``.
    try:
        logger.info(
            "scan_upload_received",
            filename=sanitize_upload_filename(file.filename),
            bytes=upload_path.stat().st_size,
        )
        job = create_scan_job()
        store.create(job)
        try:
            result = scan_archive(upload_path, config)
        except (UploadError, ScanError) as exc:
            final = fail_scan_job(job, f"{type(exc).__name__}: {exc}")
        else:
            final = complete_scan_job(job, result)
        store.update(final)
        return final
    finally:
        upload_path.unlink(missing_ok=True)


@router.get("", response_model=list[ScanJob])
def list_scans(store: ScanJobStoreDep) -> list[ScanJob]:
    """Return all scan jobs in the store's deterministic order (by created_at, then id)."""

    return list(store.list())


@router.get("/{job_id}", response_model=ScanJob)
def get_scan(job_id: str, store: ScanJobStoreDep) -> ScanJob:
    """Return one scan job; an unknown id raises ScanJobNotFoundError (mapped to HTTP 404)."""

    return store.get(job_id)
