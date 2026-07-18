"""Tests for the SARIF 2.1.0 reporting layer (Reporting Slice 2)."""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Sequence
from pathlib import Path

import pytest
from app.services.deterministic import ANALYZER_REGISTRY
from app.services.reporting import (
    ReportMetadata,
    SarifLog,
    build_sarif_report,
    render_sarif_report,
)
from app.services.scan import LanguageGroup, ScanConfig, ScanResult, ScanStatus
from app.services.upload import scan_archive
from contracts import Finding, SourceLocation
from pydantic import ValidationError

_META = ReportMetadata(tool_name="AI SAST Platform", tool_version="0.1.0", scan_id="job-1")


def _finding(
    file: str,
    line: int | None,
    *,
    cwe: str | None = "CWE-328",
    rule: str | None = "python-weak-hash",
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
    resolved: frozenset[LanguageGroup] = frozenset({LanguageGroup.PYTHON}),
) -> ScanResult:
    return ScanResult(
        status=status,
        detected_language_groups=frozenset({LanguageGroup.PYTHON}),
        resolved_language_groups=resolved,
        analyzer_runs=[],
        files_scanned=1,
        total_findings=len(findings),
        findings=list(findings),
    )


def _dump(scan_result: ScanResult, meta: ReportMetadata = _META) -> dict:
    return json.loads(render_sarif_report(scan_result, meta))


# --- log skeleton ----------------------------------------------------------------------


def test_log_skeleton() -> None:
    dumped = _dump(_result([_finding("a.py", 2)]))

    assert dumped["version"] == "2.1.0"
    assert dumped["$schema"].endswith("sarif-2.1.0.json")
    driver = dumped["runs"][0]["tool"]["driver"]
    assert driver["name"] == "AI SAST Platform"
    assert driver["version"] == "0.1.0"


def test_information_uri_included_when_provided_else_omitted() -> None:
    without = _dump(_result([]))["runs"][0]["tool"]["driver"]
    assert "informationUri" not in without

    meta = _META.model_copy(update={"information_uri": "https://example.com/sast"})
    with_uri = _dump(_result([]), meta)["runs"][0]["tool"]["driver"]
    assert with_uri["informationUri"] == "https://example.com/sast"


# --- rule catalog (registry-derived, detector-grained) ---------------------------------


def test_rule_catalog_mirrors_registry() -> None:
    rules = _dump(_result([]))["runs"][0]["tool"]["driver"]["rules"]

    assert [r["id"] for r in rules] == [e.analyzer.detector_name for e in ANALYZER_REGISTRY]
    assert all(r["name"] == r["id"] for r in rules)


def test_rule_catalog_cwe_tags() -> None:
    rules = _dump(_result([]))["runs"][0]["tool"]["driver"]["rules"]
    weak_crypto = next(r for r in rules if r["id"] == "weak-crypto-scanner")

    assert weak_crypto["properties"]["tags"] == [
        "external/cwe/cwe-327",
        "external/cwe/cwe-328",
        "security",
    ]


def test_full_catalog_present_even_with_no_results() -> None:
    dumped = _dump(_result([], status=ScanStatus.NO_SUPPORTED_LANGUAGES, resolved=frozenset()))

    assert dumped["runs"][0]["results"] == []
    assert len(dumped["runs"][0]["tool"]["driver"]["rules"]) == len(ANALYZER_REGISTRY)


def test_injected_registry_shapes_catalog() -> None:
    log = build_sarif_report(_result([]), _META, registry=ANALYZER_REGISTRY[:1])

    assert len(log.runs[0].tool.driver.rules) == 1


# --- result mapping --------------------------------------------------------------------


def test_result_mapping() -> None:
    result = _dump(_result([_finding("pkg/a.py", 2)]))["runs"][0]["results"][0]

    assert result["ruleId"] == "weak-crypto-scanner"
    assert result["ruleIndex"] == 2  # weak-crypto is 3rd in the registry
    assert result["level"] == "warning"
    location = result["locations"][0]["physicalLocation"]
    assert location["artifactLocation"]["uri"] == "pkg/a.py"
    assert location["region"] == {"startLine": 2, "endLine": 2}
    assert result["properties"] == {"rule_id": "python-weak-hash", "cwe": "CWE-328"}


def test_region_omitted_when_no_start_line() -> None:
    result = _dump(_result([_finding("a.py", None)]))["runs"][0]["results"][0]

    assert "region" not in result["locations"][0]["physicalLocation"]


def test_message_is_generic_and_hides_rule_name() -> None:
    result = _dump(_result([_finding("a.py", 2)]))["runs"][0]["results"][0]

    assert result["message"]["text"] == "Potential security issue detected (CWE-328)."
    assert "python-weak-hash" not in result["message"]["text"]


def test_message_without_cwe() -> None:
    result = _dump(_result([_finding("a.py", 2, cwe=None)]))["runs"][0]["results"][0]

    assert result["message"]["text"] == "Potential security issue detected."


def test_result_for_unknown_detector_omits_rule_index() -> None:
    result = _dump(_result([_finding("a.py", 2, detector="ghost")]))["runs"][0]["results"][0]

    assert result["ruleId"] == "ghost"
    assert "ruleIndex" not in result


def test_result_for_null_detector_uses_unknown() -> None:
    result = _dump(_result([_finding("a.py", 2, detector=None)]))["runs"][0]["results"][0]

    assert result["ruleId"] == "unknown"
    assert "ruleIndex" not in result


# --- fingerprints ----------------------------------------------------------------------


def test_fingerprint_key_and_value() -> None:
    finding = _finding("a.py", 2)
    result = _dump(_result([finding]))["runs"][0]["results"][0]

    fingerprints = result["partialFingerprints"]
    assert set(fingerprints) == {"aiSastFindingHash/v1"}
    canonical = "weak-crypto-scanner|python-weak-hash|a.py|2|2|CWE-328"
    assert fingerprints["aiSastFindingHash/v1"] == hashlib.sha256(canonical.encode()).hexdigest()


def test_fingerprint_changes_with_any_component() -> None:
    base = _finding("a.py", 2)
    variants = [
        _finding("a.py", 2, cwe="CWE-327"),
        _finding("a.py", 2, rule="other-rule"),
        _finding("a.py", 2, detector="secret-scanner"),
        _finding("b.py", 2),
        _finding("a.py", 3),
    ]
    base_fp = _dump(_result([base]))["runs"][0]["results"][0]["partialFingerprints"]

    for variant in variants:
        fp = _dump(_result([variant]))["runs"][0]["results"][0]["partialFingerprints"]
        assert fp != base_fp


# --- determinism, validity, independence -----------------------------------------------


def test_render_is_deterministic() -> None:
    findings = [_finding("a.py", 1, cwe="CWE-79"), _finding("b.py", 2)]

    assert render_sarif_report(_result(findings), _META) == render_sarif_report(
        _result(findings), _META
    )


def test_render_is_valid_json() -> None:
    rendered = render_sarif_report(_result([_finding("a.py", 2)]), _META)

    assert isinstance(json.loads(rendered), dict)
    assert rendered.endswith("\n")


def test_sarif_is_independent_of_json_report() -> None:
    dumped = _dump(_result([_finding("a.py", 2)]))

    # SARIF shape only — no keys from the JSON report envelope.
    assert "report_schema_version" not in dumped
    assert "summary" not in dumped
    assert set(dumped) == {"$schema", "version", "runs"}


def test_sarif_log_is_immutable() -> None:
    log = build_sarif_report(_result([_finding("a.py", 2)]), _META)

    assert isinstance(log, SarifLog)
    with pytest.raises(ValidationError):
        log.version = "9.9"  # type: ignore[misc]


# --- integration & no-leakage ----------------------------------------------------------


def test_sarif_from_real_scan_has_no_source_leakage(tmp_path: Path) -> None:
    archive = tmp_path / "repo.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("a.py", "import hashlib\nx = hashlib.md5(d)\n")
        zf.writestr("b.js", 'const password = "S3cr3t-Example";\n')
    scan = scan_archive(archive, ScanConfig.auto(), workspace_dir=tmp_path).scan

    rendered = render_sarif_report(scan, _META)
    dumped = json.loads(rendered)

    assert len(dumped["runs"][0]["results"]) == scan.total_findings >= 1
    # Only metadata is emitted — never source text or secret values.
    assert "hashlib" not in rendered
    assert "S3cr3t" not in rendered
    assert "password" not in rendered
