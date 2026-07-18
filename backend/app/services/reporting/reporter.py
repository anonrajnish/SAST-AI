"""Build and render the JSON scan report (Reporting Slice 1).

Pure, deterministic projection of a :class:`ScanResult` (+ caller-supplied
:class:`ReportMetadata`) into the versioned :class:`ScanReport` envelope and its canonical JSON
string. Read-only: findings are consumed in the order ``ScanResult`` already guarantees, group
lists are sorted, and count-map keys are inserted sorted — so identical inputs render identically.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable

from contracts import Finding

from app.services.scan import ScanResult

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


def build_json_report(scan_result: ScanResult, meta: ReportMetadata) -> ScanReport:
    """Project ``scan_result`` + ``meta`` into the versioned report envelope."""

    return ScanReport(
        report_schema_version=REPORT_SCHEMA_VERSION,
        tool=ReportTool(name=meta.tool_name, version=meta.tool_version),
        scan=ReportScanInfo(
            id=meta.scan_id,
            status=scan_result.status.value,
            created_at=meta.created_at,
            completed_at=meta.completed_at,
            target_label=meta.target_label,
        ),
        summary=_build_summary(scan_result),
        findings=[_to_report_finding(finding) for finding in scan_result.findings],
    )


def render_json_report(scan_result: ScanResult, meta: ReportMetadata) -> str:
    """Return the canonical JSON string for the report (deterministic; trailing newline)."""

    report = build_json_report(scan_result, meta)
    return json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"


def _to_report_finding(finding: Finding) -> ReportFinding:
    location = finding.location
    return ReportFinding(
        file=location.file,
        start_line=location.start_line,
        end_line=location.end_line,
        rule_id=finding.rule_id,
        cwe=finding.cwe,
        detector=finding.detector,
    )


def _sorted_counts(values: Iterable[str | None]) -> dict[str, int]:
    """Count non-null ``values`` into a dict whose keys are inserted in sorted order."""

    counts = Counter(value for value in values if value is not None)
    return {key: counts[key] for key in sorted(counts)}


def _build_summary(scan_result: ScanResult) -> ReportSummary:
    findings = scan_result.findings
    return ReportSummary(
        total_findings=scan_result.total_findings,
        files_scanned=scan_result.files_scanned,
        analyzers=[
            ReportAnalyzerRun(detector=run.detector_name, finding_count=run.finding_count)
            for run in scan_result.analyzer_runs
        ],
        detected_language_groups=sorted(
            group.value for group in scan_result.detected_language_groups
        ),
        resolved_language_groups=sorted(
            group.value for group in scan_result.resolved_language_groups
        ),
        cwe_counts=_sorted_counts(finding.cwe for finding in findings),
        rule_counts=_sorted_counts(finding.rule_id for finding in findings),
        detector_counts=_sorted_counts(finding.detector for finding in findings),
    )
