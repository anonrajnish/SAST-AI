"""Scan-job lifecycle + store (Slice 1-2).

An immutable, in-memory lifecycle *around* the completed upload+scan flow: a :class:`ScanJob`
owns the status and timestamps for one scan whose output is an
:class:`~app.services.upload.ArchiveScanResult`. Slice 2 adds :class:`ScanJobStore`, a
thread-safe in-memory registry that is the single source of truth for job state. The upload
subsystem and scan pipeline are unchanged. Synchronous today; the ``RUNNING`` state and the
immutable transition-function shape prepare for a future asynchronous executor. No persistence,
DB, Redis, Celery, queues, or endpoints.
"""

from __future__ import annotations

from .errors import (
    DuplicateScanJobError,
    InvalidScanJobTransitionError,
    ScanJobError,
    ScanJobNotFoundError,
)
from .lifecycle import complete_scan_job, create_scan_job, fail_scan_job
from .models import ScanJob, ScanJobResult, ScanJobStatus
from .store import ScanJobStore

__all__ = [
    "DuplicateScanJobError",
    "InvalidScanJobTransitionError",
    "ScanJob",
    "ScanJobError",
    "ScanJobNotFoundError",
    "ScanJobResult",
    "ScanJobStatus",
    "ScanJobStore",
    "complete_scan_job",
    "create_scan_job",
    "fail_scan_job",
]
