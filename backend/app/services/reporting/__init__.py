"""Reporting layer (JSON + SARIF export).

A pure, deterministic library that projects a :class:`~app.services.scan.ScanResult` (plus a
caller-supplied :class:`ReportMetadata`) into export documents: a dedicated versioned JSON report
envelope (:class:`ScanReport`, Slice 1) and a SARIF 2.1.0 log (:class:`SarifLog`, Slice 2). Both
serializers consume ``ScanResult`` directly and independently; reports carry only finding metadata
(no source snippets). REST export and persistence remain out of scope.
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
from .sarif import build_sarif_report, render_sarif_report
from .sarif_models import SarifLog

__all__ = [
    "REPORT_SCHEMA_VERSION",
    "ReportAnalyzerRun",
    "ReportFinding",
    "ReportMetadata",
    "ReportScanInfo",
    "ReportSummary",
    "ReportTool",
    "SarifLog",
    "ScanReport",
    "build_json_report",
    "build_sarif_report",
    "render_json_report",
    "render_sarif_report",
]
