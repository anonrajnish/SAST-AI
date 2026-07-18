"""Result model for repository upload & safe extraction (Slice 1)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ExtractedRepository(BaseModel):
    """The outcome of safely extracting an uploaded ZIP archive.

    ``root`` is the fresh extraction directory — the repository root a later scan will
    target. ``file_count`` / ``directory_count`` are the number of regular-file and
    directory entries written. Extracted files are inert regular files; they are never
    imported or executed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: Path
    file_count: int
    directory_count: int
