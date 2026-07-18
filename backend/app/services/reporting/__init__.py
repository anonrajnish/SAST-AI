"""Reporting layer (Slice 1: JSON export).

A pure, deterministic library that projects a :class:`~app.services.scan.ScanResult` (plus a
caller-supplied :class:`ReportMetadata`) into a dedicated, versioned JSON report envelope
(:class:`ScanReport`). Read-only; carries only finding metadata (no source snippets). SARIF, REST
export, persistence, and other formats are deliberately out of scope this slice.
"""

from __future__ import annotations

from .metadata import ReportMetadata
from .models import (
    REPORT_SCHEMA_VERSION,
    ReportAnalyzerRun,
    ReportFinding,
    ReportScanInfo,
    ReportSummary,
    ReportTool,
    ScanReport,
)
from .reporter import build_json_report, render_json_report

__all__ = [
    "REPORT_SCHEMA_VERSION",
    "ReportAnalyzerRun",
    "ReportFinding",
    "ReportMetadata",
    "ReportScanInfo",
    "ReportSummary",
    "ReportTool",
    "ScanReport",
    "build_json_report",
    "render_json_report",
]
