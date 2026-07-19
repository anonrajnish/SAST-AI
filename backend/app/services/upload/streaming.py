"""Streaming an uploaded ZIP to a temporary file with a size cap (Multipart Upload slice).

Keeps the extractor path-based and unchanged: an upload is streamed in fixed-size chunks to a
fresh temp ``.zip`` whose name the *server* chooses (the client filename is never used as a path),
capped at a byte budget. The caller owns deleting the returned file; this helper cleans up its own
partial file on any streaming error (including a client disconnect mid-upload).
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import IO

from .errors import ArchiveTooLargeError

_UPLOAD_PREFIX = "sast-upload-src-"
_ZIP_SUFFIX = ".zip"
_STREAM_CHUNK_BYTES = 64 * 1024

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")
_MAX_DISPLAY_NAME = 128
_FALLBACK_DISPLAY_NAME = "upload.zip"


def stream_zip_to_temp(
    source: IO[bytes], *, max_bytes: int, directory: Path | None = None
) -> Path:
    """Stream ``source`` to a fresh temp ``.zip`` (server-chosen name); return its path.

    Writes in chunks, enforcing a running cap of ``max_bytes`` — exceeding it raises
    :class:`ArchiveTooLargeError`. On any failure the partial temp file is removed before the
    exception propagates, so a rejected or interrupted upload leaves nothing behind. The caller
    is responsible for deleting the returned file once done with it.
    """

    fd, name = tempfile.mkstemp(prefix=_UPLOAD_PREFIX, suffix=_ZIP_SUFFIX, dir=directory)
    path = Path(name)
    written = 0
    try:
        with os.fdopen(fd, "wb") as destination:
            while True:
                chunk = source.read(_STREAM_CHUNK_BYTES)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise ArchiveTooLargeError(written, max_bytes)
                destination.write(chunk)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def sanitize_upload_filename(filename: str | None) -> str:
    """Return a safe, bounded display name for logging/audit only — never used as a path.

    Strips any directory components, replaces unsafe characters, bounds the length, and falls
    back to a fixed name when empty.
    """

    if not filename:
        return _FALLBACK_DISPLAY_NAME
    base = Path(filename).name
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", base)[:_MAX_DISPLAY_NAME]
    return cleaned or _FALLBACK_DISPLAY_NAME
