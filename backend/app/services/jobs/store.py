"""In-memory scan-job store (Slice 2).

A thread-safe registry of immutable :class:`~app.services.jobs.models.ScanJob` snapshots,
intended as the single source of truth for job state that future REST endpoints will read and
write. In-memory only — process memory, no database, persistence, Redis, or background workers.

The store keeps the jobs unchanged: it holds references to the frozen ``ScanJob`` snapshots and
returns them directly. Lifecycle transitions remain the job of
:mod:`app.services.jobs.lifecycle` (which returns a new snapshot); callers then :meth:`update`
the store with it.
"""

from __future__ import annotations

from threading import Lock

from .errors import DuplicateScanJobError, ScanJobNotFoundError
from .models import ScanJob


class ScanJobStore:
    """Thread-safe in-memory store of scan jobs keyed by ``job_id``."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScanJob] = {}
        self._lock = Lock()

    def create(self, job: ScanJob) -> None:
        """Register a new ``job``; raises :class:`DuplicateScanJobError` if the id is taken."""

        with self._lock:
            if job.job_id in self._jobs:
                raise DuplicateScanJobError(job.job_id)
            self._jobs[job.job_id] = job

    def get(self, job_id: str) -> ScanJob:
        """Return the job for ``job_id``; raises :class:`ScanJobNotFoundError` if absent."""

        with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError:
                raise ScanJobNotFoundError(job_id) from None

    def update(self, job: ScanJob) -> None:
        """Replace an existing job's snapshot; raises :class:`ScanJobNotFoundError` if absent.

        Persists a new snapshot (typically produced by a lifecycle transition) under the same
        ``job_id``. The store does not police transition validity — that is enforced by the
        lifecycle functions when the snapshot is produced.
        """

        with self._lock:
            if job.job_id not in self._jobs:
                raise ScanJobNotFoundError(job.job_id)
            self._jobs[job.job_id] = job

    def list(self) -> tuple[ScanJob, ...]:
        """Return all jobs in a deterministic order (by ``created_at``, then ``job_id``)."""

        with self._lock:
            snapshot = list(self._jobs.values())
        return tuple(sorted(snapshot, key=lambda job: (job.created_at, job.job_id)))
