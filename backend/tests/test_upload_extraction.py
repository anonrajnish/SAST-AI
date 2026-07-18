"""Tests for repository upload & safe extraction (Slice 1)."""

from __future__ import annotations

import io
import os
import stat
import zipfile
from pathlib import Path

import pytest
from app.services.upload import (
    CorruptedArchiveError,
    EncryptedArchiveError,
    ExtractedRepository,
    NestedArchiveError,
    PathTraversalError,
    SpecialFileError,
    SymlinkEntryError,
    UnsupportedArchiveError,
    extract_zip,
)


def _write_zip(path: Path, build: object) -> Path:
    """Create a ZIP at ``path`` via ``build(zf)`` and return the path."""

    with zipfile.ZipFile(path, "w") as zf:
        build(zf)  # type: ignore[operator]
    return path


def _typed_entry(name: str, *, external_attr: int = 0) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name)
    info.external_attr = external_attr
    return info


# --- valid & empty ---------------------------------------------------------------------


def test_valid_zip_extracts_files_and_dirs(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "repo.zip",
        lambda zf: (
            zf.writestr("app/main.py", "print('hi')\n"),
            zf.writestr("app/util.py", "x = 1\n"),
            zf.writestr("docs/", ""),
            zf.writestr("README.md", "# repo\n"),
        ),
    )

    result = extract_zip(archive, workspace_dir=tmp_path)

    assert isinstance(result, ExtractedRepository)
    assert result.root.is_dir()
    assert result.root.parent == tmp_path
    assert result.file_count == 3
    assert result.directory_count == 1
    assert (result.root / "app" / "main.py").read_text() == "print('hi')\n"
    assert (result.root / "docs").is_dir()


def test_extracted_files_are_not_executable(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "repo.zip", lambda zf: zf.writestr("run.py", "print('hi')\n")
    )

    result = extract_zip(archive, workspace_dir=tmp_path)

    # Files are written inert (no execute bit); nothing is ever run during extraction.
    assert not os.access(result.root / "run.py", os.X_OK)


def test_empty_zip_extracts_to_empty_dir(tmp_path: Path) -> None:
    archive = _write_zip(tmp_path / "empty.zip", lambda zf: None)

    result = extract_zip(archive, workspace_dir=tmp_path)

    assert result.file_count == 0
    assert result.directory_count == 0
    assert result.root.is_dir()
    assert list(result.root.iterdir()) == []


# --- path safety -----------------------------------------------------------------------


def test_zip_slip_is_rejected(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "slip.zip",
        lambda zf: zf.writestr(_typed_entry("../../evil.py"), "pwned\n"),
    )

    with pytest.raises(PathTraversalError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "abs.zip",
        lambda zf: zf.writestr(_typed_entry("/etc/evil.py"), "pwned\n"),
    )

    with pytest.raises(PathTraversalError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_windows_separator_is_rejected(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "win.zip",
        lambda zf: zf.writestr(_typed_entry("..\\..\\evil.py"), "pwned\n"),
    )

    with pytest.raises(PathTraversalError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_empty_entry_name_is_rejected(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "noname.zip", lambda zf: zf.writestr(_typed_entry(""), "x\n")
    )

    with pytest.raises(PathTraversalError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_rejected_archive_leaves_no_partial_extraction(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "slip.zip",
        lambda zf: zf.writestr(_typed_entry("../evil.py"), "pwned\n"),
    )

    with pytest.raises(PathTraversalError):
        extract_zip(archive, workspace_dir=tmp_path)

    # Validation happens before any temp dir is created: only the archive remains.
    assert list(tmp_path.iterdir()) == [archive]


# --- entry types -----------------------------------------------------------------------


def test_symlink_entry_is_rejected(tmp_path: Path) -> None:
    attr = (stat.S_IFLNK | 0o777) << 16
    archive = _write_zip(
        tmp_path / "link.zip",
        lambda zf: zf.writestr(_typed_entry("link", external_attr=attr), "/etc/passwd"),
    )

    with pytest.raises(SymlinkEntryError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_special_file_entry_is_rejected(tmp_path: Path) -> None:
    attr = (stat.S_IFIFO | 0o644) << 16
    archive = _write_zip(
        tmp_path / "fifo.zip",
        lambda zf: zf.writestr(_typed_entry("pipe", external_attr=attr), ""),
    )

    with pytest.raises(SpecialFileError):
        extract_zip(archive, workspace_dir=tmp_path)


# --- nested archives -------------------------------------------------------------------


def test_nested_zip_is_rejected(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "outer.zip",
        lambda zf: zf.writestr("inner.zip", b"PK\x03\x04 not really"),
    )

    with pytest.raises(NestedArchiveError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_nested_tar_gz_is_rejected(tmp_path: Path) -> None:
    archive = _write_zip(
        tmp_path / "outer.zip",
        lambda zf: zf.writestr("payload.tar.gz", b"\x1f\x8b compressed"),
    )

    with pytest.raises(NestedArchiveError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_directory_named_like_archive_is_allowed(tmp_path: Path) -> None:
    # A *directory* named like an archive is not a nested archive and must be allowed.
    archive = _write_zip(
        tmp_path / "repo.zip",
        lambda zf: (
            zf.writestr("cache.zip/", ""),
            zf.writestr("cache.zip/data.txt", "ok\n"),
        ),
    )

    result = extract_zip(archive, workspace_dir=tmp_path)

    assert (result.root / "cache.zip").is_dir()
    assert (result.root / "cache.zip" / "data.txt").read_text() == "ok\n"


# --- encryption & corruption -----------------------------------------------------------


def _set_encryption_flag(raw: bytes) -> bytes:
    """Set general-purpose bit 0 (encrypted) in each local & central header of a ZIP."""

    patched = bytearray(raw)
    # Local file header PK\x03\x04: flag at offset +6; central dir PK\x01\x02: flag at +8.
    for signature, flag_offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        start = 0
        while (index := patched.find(signature, start)) != -1:
            patched[index + flag_offset] |= 0x1
            start = index + len(signature)
    return bytes(patched)


def test_encrypted_zip_is_rejected(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("secret.txt", "cipher")

    archive = tmp_path / "enc.zip"
    archive.write_bytes(_set_encryption_flag(buffer.getvalue()))

    with pytest.raises(EncryptedArchiveError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_garbage_file_is_rejected_as_corrupted(tmp_path: Path) -> None:
    archive = tmp_path / "broken.zip"
    archive.write_bytes(b"this is definitely not a zip archive")

    with pytest.raises(CorruptedArchiveError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_bad_crc_is_rejected_as_corrupted(tmp_path: Path) -> None:
    # Build a STORED zip, then flip a data byte so the central-directory CRC no longer
    # matches — a valid container with corrupt content (caught by the pre-extraction check).
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("data.txt", "original-content")
    raw = bytearray(buffer.getvalue())
    data_offset = 30 + len("data.txt")  # local header (30) + filename, then stored data
    raw[data_offset] ^= 0xFF

    archive = tmp_path / "crc.zip"
    archive.write_bytes(raw)

    with pytest.raises(CorruptedArchiveError):
        extract_zip(archive, workspace_dir=tmp_path)


# --- container type & availability -----------------------------------------------------


def test_non_zip_extension_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "repo.tar"
    archive.write_bytes(b"whatever")

    with pytest.raises(UnsupportedArchiveError):
        extract_zip(archive, workspace_dir=tmp_path)


def test_missing_archive_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(CorruptedArchiveError):
        extract_zip(tmp_path / "does-not-exist.zip", workspace_dir=tmp_path)


# --- failure cleanup -------------------------------------------------------------------


def test_unexpected_extraction_failure_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _write_zip(
        tmp_path / "repo.zip", lambda zf: zf.writestr("a.py", "x = 1\n")
    )

    def _boom(src: object, dst: object, written: int, limit: int) -> int:
        raise RuntimeError("disk full")

    monkeypatch.setattr("app.services.upload.extractor._copy_with_limit", _boom)

    with pytest.raises(RuntimeError):
        extract_zip(archive, workspace_dir=tmp_path)

    # The half-written temp dir is removed on failure; only the archive remains.
    assert list(tmp_path.iterdir()) == [archive]
