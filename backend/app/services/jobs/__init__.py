"""Scan-job lifecycle (Slice 1).

An immutable, in-memory lifecycle *around* the completed upload+scan flow: a :class:`ScanJob`
owns the status and timestamps for one scan whose output is an
:class:`~app.services.upload.ArchiveScanResult`. The upload subsystem and scan pipeline are
unchanged. Synchronous today; the ``RUNNING`` state and the immutable transition-function shape
prepare for a future asynchronous executor. No persistence, DB, Celery, queues, or endpoints.
"""

from __future__ import annotations

from .errors import InvalidScanJobTransitionError, ScanJobError
from .lifecycle import complete_scan_job, create_scan_job, fail_scan_job
from .models import ScanJob, ScanJobResult, ScanJobStatus

__all__ = [
    "InvalidScanJobTransitionError",
    "ScanJob",
    "ScanJobError",
    "ScanJobResult",
    "ScanJobStatus",
    "complete_scan_job",
    "create_scan_job",
    "fail_scan_job",
]
