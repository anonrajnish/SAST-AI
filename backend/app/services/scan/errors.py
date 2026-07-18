"""Typed errors for the scan pipeline (Slice 3)."""

from __future__ import annotations


class ScanError(Exception):
    """Base class for scan-pipeline errors."""


class RepositoryError(ScanError):
    """The repository root is missing or is not a directory."""


class ScanExecutionError(ScanError):
    """An analyzer raised an unexpected error during scanning (fail-fast).

    Carries the offending analyzer's ``detector_name`` for diagnosability; the original
    exception is chained as ``__cause__``.
    """

    def __init__(self, detector_name: str, cause: BaseException) -> None:
        super().__init__(f"analyzer {detector_name!r} failed during scan: {cause}")
        self.detector_name = detector_name
