"""Tests for deterministic scan-finding ordering (Slice 4)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from app.services.scan import (
    ScanConfig,
    ScanResult,
    ScanStatus,
    order_findings,
    scan_repository,
)
from contracts import Finding, SourceLocation


def _finding(
    file: str, line: int, *, detector: str = "d", rule: str = "r", cwe: str = "CWE-798"
) -> Finding:
    return Finding(
        location=SourceLocation(file=file, start_line=line, end_line=line),
        cwe=cwe,
        rule_id=rule,
        detector=detector,
    )


def test_order_findings_sorts_by_metadata() -> None:
    unordered = [_finding("b.py", 1), _finding("a.py", 5), _finding("a.py", 2)]
    ordered = order_findings(unordered)
    assert [(f.location.file, f.location.start_line) for f in ordered] == [
        ("a.py", 2),
        ("a.py", 5),
        ("b.py", 1),
    ]


def test_order_findings_tiebreaks_on_detector_then_rule() -> None:
    a = _finding("a.py", 1, detector="alpha", rule="r2")
    b = _finding("a.py", 1, detector="alpha", rule="r1")
    c = _finding("a.py", 1, detector="beta", rule="r0")
    ordered = order_findings([c, a, b])
    assert [(f.detector, f.rule_id) for f in ordered] == [
        ("alpha", "r1"),
        ("alpha", "r2"),
        ("beta", "r0"),
    ]


def test_order_findings_is_stable_for_equal_keys() -> None:
    first = _finding("a.py", 1)
    second = _finding("a.py", 1)
    assert order_findings([first, second]) == [first, second]


def test_scan_result_orders_findings_on_construction() -> None:
    result = ScanResult(
        status=ScanStatus.COMPLETED,
        detected_language_groups=frozenset(),
        resolved_language_groups=frozenset(),
        analyzer_runs=[],
        files_scanned=0,
        total_findings=2,
        findings=[_finding("z.py", 1), _finding("a.py", 1)],
    )
    assert [f.location.file for f in result.findings] == ["a.py", "z.py"]


def test_pipeline_result_is_globally_ordered_by_path(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    # a.py is flagged by weak-crypto (3rd analyzer); b.py by secret-scanner (1st).
    write_file(tmp_path / "a.py", "import hashlib\nx = hashlib.md5(d)\n")
    write_file(tmp_path / "b.py", 'password = "S3cr3t-Example"\n')

    result = scan_repository(tmp_path, ScanConfig.auto())
    files = [f.location.file for f in result.findings]

    assert files == sorted(files)  # path-first order, not analyzer/registry order
    assert files[0] == "a.py"


def test_result_serialization_is_stable_across_runs(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "import hashlib\nx = hashlib.md5(d)\n")
    write_file(tmp_path / "b.js", 'const password = "S3cr3t-Example";\n')

    first = scan_repository(tmp_path, ScanConfig.auto()).model_dump(mode="json")
    second = scan_repository(tmp_path, ScanConfig.auto()).model_dump(mode="json")

    assert json.dumps(first) == json.dumps(second)


def test_group_sets_serialize_sorted(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "x = 1\n")
    write_file(tmp_path / "b.js", "const a = 1;\n")

    dumped = scan_repository(tmp_path, ScanConfig.auto()).model_dump(mode="json")

    assert dumped["detected_language_groups"] == ["python", "web"]
    assert dumped["resolved_language_groups"] == ["python", "web"]
