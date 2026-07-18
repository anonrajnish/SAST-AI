"""Typed errors for the scan-job lifecycle and store (Slice 1-2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ScanJobStatus


class ScanJobError(Exception):
    """Base class for scan-job lifecycle and store errors."""


class DuplicateScanJobError(ScanJobError):
    """A job with the same ``job_id`` already exists in the store."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"scan job already exists: {job_id!r}")
        self.job_id = job_id


class ScanJobNotFoundError(ScanJobError):
    """No job with the requested ``job_id`` exists in the store."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"scan job not found: {job_id!r}")
        self.job_id = job_id


class InvalidScanJobTransitionError(ScanJobError):
    """A lifecycle transition was attempted from a state that does not allow it.

    Carries the job's ``current_status`` and the ``attempted`` transition verb for
    diagnosability (e.g. completing an already-terminal job).
    """

    def __init__(self, current_status: ScanJobStatus, attempted: str) -> None:
        super().__init__(
            f"cannot {attempted} a scan job in terminal state {current_status.value!r}"
        )
        self.current_status = current_status
        self.attempted = attempted
