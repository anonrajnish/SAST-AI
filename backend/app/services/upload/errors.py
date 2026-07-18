"""Typed errors for repository upload & safe extraction (Slice 1)."""

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
