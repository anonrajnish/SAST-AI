"""Tests for the JSON reporting layer (Reporting Slice 1)."""

from __future__ import annotations

import json
import zipfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.reporting import (
    REPORT_SCHEMA_VERSION,
    ReportAnalyzerRun,
    ReportMetadata,
    ScanReport,
    build_json_report,
    render_json_report,
)
from app.services.scan import (
    AnalyzerRun,
    LanguageGroup,
    ScanConfig,
    ScanResult,
    ScanStatus,
)
from app.services.upload import scan_archive
from contracts import Finding, SourceLocation
from pydantic import ValidationError

_META = ReportMetadata(
    tool_name="AI SAST Platform",
    tool_version="0.1.0",
    scan_id="job-1",
    created_at=datetime(2026, 7, 19, 12, 0, 0, tzinfo=UTC),
    completed_at=datetime(2026, 7, 19, 12, 0, 5, tzinfo=UTC),
    target_label="repo.zip",
)

_FINDING_KEYS = {"file", "start_line", "end_line", "rule_id", "cwe", "detector"}


def _finding(
    file: str,
    line: int,
    *,
    cwe: str | None = "CWE-328",
    rule: str | None = "weak-hash",
    detector: str | None = "weak-crypto-scanner",
) -> Finding:
    return Finding(
        location=SourceLocation(file=file, start_line=line, end_line=line),
        cwe=cwe,
        rule_id=rule,
        detector=detector,
    )


def _result(
    findings: Sequence[Finding],
    *,
    status: ScanStatus = ScanStatus.COMPLETED,
    detected: frozenset[LanguageGroup] = frozenset({LanguageGroup.PYTHON}),
    resolved: frozenset[LanguageGroup] = frozenset({LanguageGroup.PYTHON}),
    analyzers: list[AnalyzerRun] | None = None,
    files_scanned: int = 1,
) -> ScanResult:
    return ScanResult(
        status=status,
        detected_language_groups=detected,
        resolved_language_groups=resolved,
        analyzer_runs=analyzers if analyzers is not None else [],
        files_scanned=files_scanned,
        total_findings=len(findings),
        findings=list(findings),
    )


# --- structure & metadata --------------------------------------------------------------


def test_report_structure_and_metadata() -> None:
    report = build_json_report(_result([_finding("a.py", 2)]), _META)

    assert isinstance(report, ScanReport)
    assert report.report_schema_version == REPORT_SCHEMA_VERSION == "1.0"
    assert report.tool.name == "AI SAST Platform"
    assert report.tool.version == "0.1.0"
    assert report.scan.id == "job-1"
    assert report.scan.status == "completed"
    assert report.scan.target_label == "repo.zip"
    assert report.scan.created_at == _META.created_at


def test_metadata_serializes_timestamps_as_iso() -> None:
    dumped = json.loads(render_json_report(_result([]), _META))

    assert isinstance(dumped["scan"]["created_at"], str)
    assert dumped["scan"]["completed_at"].startswith("2026-07-19T12:00:05")


# --- summary counts --------------------------------------------------------------------


def test_summary_counts_by_cwe_rule_and_detector() -> None:
    findings = [
        _finding("a.py", 2, cwe="CWE-328", rule="weak-hash", detector="weak-crypto-scanner"),
        _finding("b.py", 3, cwe="CWE-328", rule="weak-hash", detector="weak-crypto-scanner"),
        _finding("c.py", 4, cwe="CWE-327", rule="weak-cipher", detector="weak-crypto-scanner"),
    ]
    analyzers = [AnalyzerRun(detector_name="weak-crypto-scanner", finding_count=3)]

    summary = build_json_report(
        _result(findings, analyzers=analyzers, files_scanned=3), _META
    ).summary

    assert summary.total_findings == 3
    assert summary.files_scanned == 3
    assert summary.analyzers == [
        ReportAnalyzerRun(detector="weak-crypto-scanner", finding_count=3)
    ]
    assert summary.cwe_counts == {"CWE-327": 1, "CWE-328": 2}
    assert summary.rule_counts == {"weak-cipher": 1, "weak-hash": 2}
    assert summary.detector_counts == {"weak-crypto-scanner": 3}


def test_summary_language_groups_are_sorted() -> None:
    summary = build_json_report(
        _result(
            [],
            detected=frozenset({LanguageGroup.WEB, LanguageGroup.PYTHON}),
            resolved=frozenset({LanguageGroup.PYTHON}),
        ),
        _META,
    ).summary

    assert summary.detected_language_groups == ["python", "web"]
    assert summary.resolved_language_groups == ["python"]


def test_count_map_keys_are_sorted() -> None:
    findings = [
        _finding("a.py", 1, cwe="CWE-79"),
        _finding("b.py", 2, cwe="CWE-502"),
        _finding("c.py", 3, cwe="CWE-327"),
    ]
    summary = build_json_report(_result(findings), _META).summary

    assert list(summary.cwe_counts) == ["CWE-327", "CWE-502", "CWE-79"]


def test_null_metadata_excluded_from_counts_but_present_in_findings() -> None:
    findings = [_finding("a.py", 1, cwe=None, rule=None, detector=None)]

    report = build_json_report(_result(findings), _META)

    assert report.summary.cwe_counts == {}
    assert report.summary.rule_counts == {}
    assert report.summary.detector_counts == {}
    assert len(report.findings) == 1
    assert report.findings[0].cwe is None


# --- findings projection ---------------------------------------------------------------


def test_findings_order_preserved_from_scan_result() -> None:
    scan_result = _result([_finding("z.py", 1), _finding("a.py", 1)])

    report = build_json_report(scan_result, _META)

    # ScanResult normalizes order; the report preserves exactly that order.
    assert [f.file for f in report.findings] == [f.location.file for f in scan_result.findings]
    assert [f.file for f in report.findings] == ["a.py", "z.py"]


def test_finding_entries_expose_only_metadata_keys() -> None:
    dumped = json.loads(render_json_report(_result([_finding("a.py", 2)]), _META))

    for entry in dumped["findings"]:
        assert set(entry) == _FINDING_KEYS


# --- serialization ---------------------------------------------------------------------


def test_render_is_valid_json_and_round_trips() -> None:
    report = build_json_report(_result([_finding("a.py", 2)]), _META)
    rendered = render_json_report(_result([_finding("a.py", 2)]), _META)

    assert json.loads(rendered) == report.model_dump(mode="json")
    assert rendered.endswith("\n")


def test_render_is_deterministic() -> None:
    findings = [_finding("a.py", 1, cwe="CWE-79"), _finding("b.py", 2, cwe="CWE-327")]

    first = render_json_report(_result(findings), _META)
    second = render_json_report(_result(findings), _META)

    assert first == second


# --- status handling -------------------------------------------------------------------


def test_no_supported_languages_yields_empty_report() -> None:
    scan_result = _result(
        [],
        status=ScanStatus.NO_SUPPORTED_LANGUAGES,
        resolved=frozenset(),
        files_scanned=0,
    )
    report = build_json_report(scan_result, _META)

    assert report.scan.status == "no_supported_languages"
    assert report.findings == []
    assert report.summary.total_findings == 0
    assert report.summary.analyzers == []
    assert report.summary.cwe_counts == {}
    assert report.summary.detector_counts == {}


# --- immutability ----------------------------------------------------------------------


def test_report_models_are_immutable() -> None:
    report = build_json_report(_result([_finding("a.py", 2)]), _META)

    with pytest.raises(ValidationError):
        report.report_schema_version = "9.9"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        _META.tool_name = "x"  # type: ignore[misc]


# --- integration: report from a real scan ----------------------------------------------


def test_report_from_real_scan(tmp_path: Path) -> None:
    archive = tmp_path / "repo.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("a.py", "import hashlib\nx = hashlib.md5(d)\n")
    scan = scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path).scan

    report = build_json_report(scan, _META)

    assert report.summary.total_findings >= 1
    assert report.summary.detector_counts.get("weak-crypto-scanner", 0) >= 1
    assert any(f.file == "a.py" for f in report.findings)
    # Fully JSON-serializable end to end.
    assert json.loads(render_json_report(scan, _META))["summary"]["total_findings"] >= 1
