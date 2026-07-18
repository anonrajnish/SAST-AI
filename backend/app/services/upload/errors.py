"""Typed errors for repository upload & safe extraction (Slice 1, 3)."""

from __future__ import annotations


class UploadError(Exception):
    """Base class for repository-upload / archive-extraction errors."""


class UnsupportedArchiveError(UploadError):
    """The upload is not a supported archive type (only ZIP is accepted)."""


class CorruptedArchiveError(UploadError):
    """The archive is missing, truncated, or not a readable/valid ZIP file."""


class EncryptedArchiveError(UploadError):
    """The ZIP archive is encrypted / password-protected and is refused."""


class UnsafeArchiveEntryError(UploadError):
    """Base class for a rejected archive entry; carries the offending entry name."""

    def __init__(self, entry_name: str, reason: str) -> None:
        super().__init__(f"unsafe archive entry {entry_name!r}: {reason}")
        self.entry_name = entry_name
        self.reason = reason


class PathTraversalError(UnsafeArchiveEntryError):
    """An entry uses an absolute path or escapes the extraction directory (Zip Slip)."""


class SymlinkEntryError(UnsafeArchiveEntryError):
    """An entry is a symbolic link, which is refused."""


class SpecialFileError(UnsafeArchiveEntryError):
    """An entry is a non-regular special file (device, FIFO, socket, ...)."""


class NestedArchiveError(UnsafeArchiveEntryError):
    """An entry is itself an archive; nested archives are refused."""


class ResourceLimitError(UploadError):
    """Base class for a configured extraction resource limit being exceeded.

    Carries the offending ``actual`` measurement and the configured ``limit`` (bytes, entry
    count, or ratio) for diagnosability. Guards against ZIP-bomb / resource-exhaustion attacks.
    """

    def __init__(self, message: str, *, actual: float, limit: float) -> None:
        super().__init__(message)
        self.actual = actual
        self.limit = limit


class ArchiveTooLargeError(ResourceLimitError):
    """The archive file on disk exceeds the maximum allowed size."""

    def __init__(self, actual: int, limit: int) -> None:
        super().__init__(
            f"archive size {actual} bytes exceeds limit {limit} bytes",
            actual=actual,
            limit=limit,
        )


class ExtractedSizeLimitError(ResourceLimitError):
    """The total uncompressed size exceeds the maximum allowed extracted size."""

    def __init__(self, actual: int, limit: int) -> None:
        super().__init__(
            f"extracted size {actual} bytes exceeds limit {limit} bytes",
            actual=actual,
            limit=limit,
        )


class FileCountLimitError(ResourceLimitError):
    """The archive contains more member entries than allowed."""

    def __init__(self, actual: int, limit: int) -> None:
        super().__init__(
            f"archive entry count {actual} exceeds limit {limit}",
            actual=actual,
            limit=limit,
        )


class CompressionRatioLimitError(ResourceLimitError):
    """The archive's compression ratio exceeds the maximum allowed (ZIP-bomb guard)."""

    def __init__(self, actual: float, limit: float) -> None:
        super().__init__(
            f"compression ratio {actual:.1f}:1 exceeds limit {limit:.1f}:1",
            actual=actual,
            limit=limit,
        )
