"""The dedicated, versioned JSON report envelope (Reporting Slice 1).

A public export contract intentionally decoupled from the internal :class:`ScanResult` shape so
it can version independently (``report_schema_version``) — internal pipeline refactors do not
silently break report consumers. All models are frozen, fully typed, and JSON-serializable, and
carry only metadata (file/location/rule_id/cwe/detector) — never source snippets or matched text.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

# Version of the report envelope schema below — distinct from the tool's own version.
REPORT_SCHEMA_VERSION = "1.0"


class ReportTool(BaseModel):
    """The tool that produced the report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    version: str


class ReportScanInfo(BaseModel):
    """Run identity/context for the scan being reported."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str | None
    status: str
    created_at: datetime | None
    completed_at: datetime | None
    target_label: str | None


class ReportAnalyzerRun(BaseModel):
    """Per-analyzer contribution to the scan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    detector: str
    finding_count: int


class ReportSummary(BaseModel):
    """Aggregate view of the scan. Count maps have sorted keys and omit null values."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_findings: int
    files_scanned: int
    analyzers: list[ReportAnalyzerRun]
    detected_language_groups: list[str]
    resolved_language_groups: list[str]
    cwe_counts: dict[str, int]
    rule_counts: dict[str, int]
    detector_counts: dict[str, int]


class ReportFinding(BaseModel):
    """A single finding, flattened to the public export shape (no source text)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    file: str
    start_line: int | None
    end_line: int | None
    rule_id: str | None
    cwe: str | None
    detector: str | None


class ScanReport(BaseModel):
    """The versioned JSON report envelope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_schema_version: str
    tool: ReportTool
    scan: ReportScanInfo
    summary: ReportSummary
    findings: list[ReportFinding]
