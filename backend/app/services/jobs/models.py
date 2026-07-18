"""Immutable scan-job lifecycle models (Slice 1).

A :class:`ScanJob` is an immutable snapshot of one scan's lifecycle *around* an
:class:`~app.services.upload.ArchiveScanResult` — it owns the status and timestamps without
changing how extraction or scanning work. The status vocabulary aligns with the architecture's
``scans.status`` (pending / running / completed / failed; ``cancelled`` is deferred with
cancellation). Execution is synchronous today; ``RUNNING`` is reserved so a future asynchronous
executor can mark a job in progress without a model change.

All models are frozen (immutable), fully typed, JSON-serializable, and deterministic: given the
same field values they serialize identically.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.upload import ArchiveScanResult


class ScanJobStatus(StrEnum):
    """Lifecycle state of a scan job (subset of the architecture's ``scans.status``)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


_TERMINAL_STATES = frozenset({ScanJobStatus.COMPLETED, ScanJobStatus.FAILED})


class ScanJobResult(BaseModel):
    """The successful terminal payload of a scan job: the archive scan output.

    A thin, immutable wrapper around :class:`~app.services.upload.ArchiveScanResult`, kept
    distinct so job-level result metadata can grow here without disturbing the scan output.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    scan: ArchiveScanResult


class ScanJob(BaseModel):
    """Immutable snapshot of one scan job's lifecycle.

    ``PENDING``/``RUNNING`` jobs carry no result, error, or ``completed_at``. A ``COMPLETED``
    job carries a :class:`ScanJobResult` and ``completed_at``; a ``FAILED`` job carries an
    ``error`` message and ``completed_at``. Transitions are performed by the lifecycle
    functions, each returning a new snapshot (see :mod:`app.services.jobs.lifecycle`).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str
    status: ScanJobStatus
    created_at: datetime
    completed_at: datetime | None = None
    result: ScanJobResult | None = None
    error: str | None = None

    @property
    def is_terminal(self) -> bool:
        """True when the job has reached a terminal state (``COMPLETED`` or ``FAILED``)."""

        return self.status in _TERMINAL_STATES

    @model_validator(mode="after")
    def _check_state_consistency(self) -> Self:
        """Enforce the state machine's invariants so no inconsistent job can exist."""

        if self.is_terminal and self.completed_at is None:
            raise ValueError(f"a {self.status.value} scan job must record completed_at")
        if not self.is_terminal and self.completed_at is not None:
            raise ValueError(f"a {self.status.value} scan job must not record completed_at")
        if self.status is ScanJobStatus.COMPLETED and self.result is None:
            raise ValueError("a completed scan job must carry a result")
        if self.status is not ScanJobStatus.COMPLETED and self.result is not None:
            raise ValueError("only a completed scan job may carry a result")
        if self.status is ScanJobStatus.FAILED and not self.error:
            raise ValueError("a failed scan job must carry an error message")
        if self.status is not ScanJobStatus.FAILED and self.error is not None:
            raise ValueError("only a failed scan job may carry an error message")
        return self
