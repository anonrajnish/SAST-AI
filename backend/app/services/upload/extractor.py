"""Repository upload & safe extraction (Slice 1).

Validates an uploaded ZIP archive and extracts it into a fresh temporary working directory,
returning the extracted repository root. Defends against Zip Slip / path traversal, absolute
paths, symlink and special-file entries, nested archives, and encrypted or corrupted
archives. The archive is opened read-only; only regular files and directories are written,
and nothing is ever imported or executed.

Scope (Slice 1): ZIP only. The archive is fully validated *before* anything is written, so a
rejected upload never leaves a partial extraction. Resource / ZIP-bomb limits, cleanup
scheduling, and scan-pipeline integration are deliberately out of scope (later slices).
"""

from __future__ import annotations

import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from .errors import (
    CorruptedArchiveError,
    EncryptedArchiveError,
    NestedArchiveError,
    PathTraversalError,
    SpecialFileError,
    SymlinkEntryError,
    UnsupportedArchiveError,
)
from .models import ExtractedRepository

_ZIP_SUFFIX = ".zip"
_WORKSPACE_PREFIX = "sast-upload-"

# ZIP general-purpose bit 0 set => the entry's data is encrypted / password-protected.
_ENCRYPTED_FLAG = 0x1

# Nested-archive suffixes refused inside an upload: an uploaded repository is expected to be
# source, not a bundle of further archives to unpack (also keeps us clear of archive bombs).
_NESTED_ARCHIVE_SUFFIXES: frozenset[str] = frozenset(
    {
        ".zip", ".tar", ".gz", ".tgz", ".bz2", ".tbz2", ".xz", ".txz",
        ".7z", ".rar", ".lz", ".lzma", ".z", ".cab", ".iso", ".ar",
        ".jar", ".war", ".gzip",
    }
)


def extract_zip(
    archive_path: Path, *, workspace_dir: Path | None = None
) -> ExtractedRepository:
    """Validate and safely extract a ZIP ``archive_path``; return the extracted repo root.

    The archive is opened read-only and fully validated *before* anything is written. On any
    security or integrity violation a typed :class:`~app.services.upload.errors.UploadError`
    subclass is raised and no partial extraction is left behind. A fresh temporary directory
    is created under ``workspace_dir`` (the system temp dir when ``None``).
    """

    _require_zip_container(archive_path)

    try:
        with zipfile.ZipFile(archive_path) as zf:
            infos = zf.infolist()
            _validate_entries(infos)
            _reject_corrupted(zf)
            return _extract(zf, infos, workspace_dir)
    except zipfile.BadZipFile as exc:
        raise CorruptedArchiveError(f"not a valid ZIP archive: {archive_path}") from exc


def _require_zip_container(archive_path: Path) -> None:
    """Reject a non-file path (missing/unreadable) or a non-``.zip`` extension."""

    if not archive_path.is_file():
        raise CorruptedArchiveError(f"archive path is not a readable file: {archive_path}")
    if archive_path.suffix.lower() != _ZIP_SUFFIX:
        raise UnsupportedArchiveError(
            f"unsupported archive type {archive_path.suffix!r}; only .zip is accepted"
        )


def _validate_entries(infos: list[zipfile.ZipInfo]) -> None:
    """Reject any unsafe entry (encrypted, symlink/special, nested archive, unsafe path)."""

    for info in infos:
        _reject_encrypted(info)
        _reject_symlink_or_special(info)
        _reject_nested_archive(info)
        _safe_relative_name(info.filename)


def _reject_encrypted(info: zipfile.ZipInfo) -> None:
    if info.flag_bits & _ENCRYPTED_FLAG:
        raise EncryptedArchiveError(f"encrypted ZIP entry: {info.filename!r}")


def _reject_symlink_or_special(info: zipfile.ZipInfo) -> None:
    """Reject symlink entries and non-regular special files (FIFO/device/socket)."""

    file_type = stat.S_IFMT(info.external_attr >> 16)
    if file_type == stat.S_IFLNK:
        raise SymlinkEntryError(info.filename, "symbolic link")
    # A missing unix mode (0) is allowed and treated by name (regular file vs. directory).
    if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise SpecialFileError(info.filename, "non-regular special file")


def _reject_nested_archive(info: zipfile.ZipInfo) -> None:
    if info.is_dir():
        return
    suffix = PurePosixPath(info.filename).suffix.lower()
    if suffix in _NESTED_ARCHIVE_SUFFIXES:
        raise NestedArchiveError(info.filename, f"nested archive ({suffix})")


def _safe_relative_name(name: str) -> PurePosixPath:
    """Return ``name`` as a safe repo-relative path, or raise :class:`PathTraversalError`.

    Rejects empty/NUL names, absolute paths, Windows-style separators/drive letters, and any
    ``..`` component. The result is guaranteed to stay within the (freshly created, symlink-free)
    extraction directory when joined to it.
    """

    if not name or "\x00" in name:
        raise PathTraversalError(name, "empty or NUL byte in entry name")
    if "\\" in name or (len(name) >= 2 and name[1] == ":"):
        raise PathTraversalError(name, "Windows-style path separator or drive letter")
    pure = PurePosixPath(name)
    if pure.is_absolute():
        raise PathTraversalError(name, "absolute path")
    if ".." in pure.parts:
        raise PathTraversalError(name, "path traversal ('..')")
    return pure


def _reject_corrupted(zf: zipfile.ZipFile) -> None:
    """Reject an archive whose data fails its CRC check (integrity, before extraction)."""

    bad = zf.testzip()
    if bad is not None:
        raise CorruptedArchiveError(f"CRC check failed for ZIP entry: {bad!r}")


def _extract(
    zf: zipfile.ZipFile, infos: list[zipfile.ZipInfo], workspace_dir: Path | None
) -> ExtractedRepository:
    """Write the already-validated entries into a fresh temp dir; clean up on any failure."""

    dest = Path(tempfile.mkdtemp(prefix=_WORKSPACE_PREFIX, dir=workspace_dir))
    file_count = 0
    directory_count = 0
    try:
        for info in infos:
            target = dest / _safe_relative_name(info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                directory_count += 1
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                file_count += 1
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise

    return ExtractedRepository(
        root=dest, file_count=file_count, directory_count=directory_count
    )
