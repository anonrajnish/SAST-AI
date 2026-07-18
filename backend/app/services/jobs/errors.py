"""Typed errors for the scan-job lifecycle (Slice 1)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ScanJobStatus


class ScanJobError(Exception):
    """Base class for scan-job lifecycle errors."""


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
