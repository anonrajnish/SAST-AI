"""Repository upload & safe extraction subsystem.

Slice 1: :func:`extract_zip` validates and safely extracts an uploaded ZIP archive into a
fresh temporary working directory, returning an :class:`ExtractedRepository`. Every failure
mode is a typed :class:`UploadError` subclass. ZIP only; deterministic; the archive is read
read-only and extracted files are never imported or executed.

Slice 2: :func:`scan_archive` orchestrates the completed scan pipeline over an uploaded ZIP
(``extract_zip`` -> ``scan_repository``), returning both results in one :class:`ArchiveScanResult`.
"""

from __future__ import annotations

from .errors import (
    ArchiveTooLargeError,
    CompressionRatioLimitError,
    CorruptedArchiveError,
    EncryptedArchiveError,
    ExtractedSizeLimitError,
    FileCountLimitError,
    NestedArchiveError,
    PathTraversalError,
    ResourceLimitError,
    SpecialFileError,
    SymlinkEntryError,
    UnsafeArchiveEntryError,
    UnsupportedArchiveError,
    UploadError,
)
from .extractor import extract_zip
from .limits import ExtractionLimits
from .models import ExtractedRepository
from .orchestration import ArchiveScanResult, scan_archive

__all__ = [
    "ArchiveScanResult",
    "ArchiveTooLargeError",
    "CompressionRatioLimitError",
    "CorruptedArchiveError",
    "EncryptedArchiveError",
    "ExtractedRepository",
    "ExtractedSizeLimitError",
    "ExtractionLimits",
    "FileCountLimitError",
    "NestedArchiveError",
    "PathTraversalError",
    "ResourceLimitError",
    "SpecialFileError",
    "SymlinkEntryError",
    "UnsafeArchiveEntryError",
    "UnsupportedArchiveError",
    "UploadError",
    "extract_zip",
    "scan_archive",
]
