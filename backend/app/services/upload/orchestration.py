"""Upload -> scan orchestration (Repository Upload Slice 2).

Coordinates the two existing subsystems for a one-call "scan a ZIP" flow:

    ZIP archive -> extract_zip() -> scan_repository() -> ArchiveScanResult

Orchestration only: it adds no extraction or scanning logic of its own and introduces no new
exceptions. ``UploadError`` (extraction) and ``RepositoryError`` / ``ScanExecutionError``
(scanning) propagate unchanged.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.services.scan import ScanConfig, ScanResult, scan_repository

from .extractor import extract_zip
from .models import ExtractedRepository


class ArchiveScanResult(BaseModel):
    """The combined outcome of extracting and then scanning one uploaded ZIP archive.

    Composes the two existing immutable result models unchanged: the extraction metadata
    (:class:`ExtractedRepository`) and the deterministic scan outcome
    (:class:`~app.services.scan.ScanResult`). JSON-serializable.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    extraction: ExtractedRepository
    scan: ScanResult


def scan_archive(
    archive_path: Path,
    config: ScanConfig,
    *,
    workspace_dir: Path | None = None,
) -> ArchiveScanResult:
    """Safely extract ``archive_path`` and scan the extracted repository root.

    Reuses :func:`~app.services.upload.extractor.extract_zip` and then
    :func:`~app.services.scan.scan_repository` unchanged, returning both the extraction
    metadata and the :class:`~app.services.scan.ScanResult` together. Extraction and scan
    errors propagate unchanged (no wrapper exceptions). ``workspace_dir`` (default: system
    temp) is a dependency-injection seam forwarded to extraction.
    """

    extraction = extract_zip(archive_path, workspace_dir=workspace_dir)
    result = scan_repository(extraction.root, config)
    return ArchiveScanResult(extraction=extraction, scan=result)
