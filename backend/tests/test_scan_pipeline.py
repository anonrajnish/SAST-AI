"""Integration tests for the scan-pipeline entry point (Slice 3)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from app.services.deterministic import AnalyzerEntry
from app.services.deterministic.analyzer import PatternAnalyzer
from app.services.scan import (
    LanguageGroup,
    RepositoryError,
    ScanConfig,
    ScanExecutionError,
    ScanResult,
    ScanStatus,
    scan_repository,
)
from contracts import Finding, SourceLocation

_PY = LanguageGroup.PYTHON
_WEB = LanguageGroup.WEB


class _RaisingAnalyzer(PatternAnalyzer):
    """A registry-shaped analyzer whose scan always fails, for the fail-fast test."""

    def __init__(self) -> None:
        super().__init__((), "raising-analyzer")

    def scan(self, corpus_root: Path) -> list[Finding]:
        raise RuntimeError("boom")


class _UnknownLanguageFindingAnalyzer(PatternAnalyzer):
    """Emits a finding for a file with no recognized language (must be scoped out)."""

    def __init__(self) -> None:
        super().__init__((), "unknown-language-analyzer")

    def scan(self, corpus_root: Path) -> list[Finding]:
        location = SourceLocation(file="weird.unknown", start_line=1, end_line=1)
        return [Finding(location=location, cwe="CWE-798", detector=self.detector_name)]


def test_auto_completed_scan_finds_python_vuln(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "hash.py", "import hashlib\nx = hashlib.md5(data)\n")

    result = scan_repository(tmp_path, ScanConfig.auto())

    assert isinstance(result, ScanResult)
    assert result.status is ScanStatus.COMPLETED
    assert result.detected_language_groups == frozenset({_PY})
    assert result.resolved_language_groups == frozenset({_PY})
    # the five Python-applicable analyzers ran (reverse-tabnabbing is Web-only)
    assert [r.detector_name for r in result.analyzer_runs] == [
        "secret-scanner",
        "code-execution-scanner",
        "weak-crypto-scanner",
        "unsafe-deserialization-scanner",
        "tls-verification-scanner",
    ]
    assert result.files_scanned == 1
    assert result.total_findings == len(result.findings) >= 1
    assert any(f.cwe == "CWE-328" for f in result.findings)  # weak MD5 hash


def test_no_supported_languages_result(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "README.md", "# docs\n")
    write_file(tmp_path / "notes.txt", "hello\n")

    result = scan_repository(tmp_path, ScanConfig.auto())

    assert result.status is ScanStatus.NO_SUPPORTED_LANGUAGES
    assert result.resolved_language_groups == frozenset()
    assert result.analyzer_runs == []
    assert result.findings == []
    assert result.files_scanned == 0
    assert result.total_findings == 0


def test_manual_scope_ignores_other_languages(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", 'password = "S3cr3t-Example"\n')
    write_file(tmp_path / "b.js", 'const password = "S3cr3t-Example";\n')
    write_file(tmp_path / "docs" / "README.md", "# docs\n")  # subdir + unsupported file

    result = scan_repository(tmp_path, ScanConfig.manual({_PY}))

    assert result.status is ScanStatus.COMPLETED
    assert result.resolved_language_groups == frozenset({_PY})
    assert result.total_findings >= 1
    # the JavaScript secret is ignored under a Python-only selection
    assert all(f.location.file.endswith(".py") for f in result.findings)
    assert result.files_scanned == 1  # only a.py is in scope (b.js/README.md excluded)


def test_manual_web_selects_web_files(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", 'password = "S3cr3t-Example"\n')
    write_file(tmp_path / "b.js", 'const password = "S3cr3t-Example";\n')

    result = scan_repository(tmp_path, ScanConfig.manual({_WEB}))

    assert result.status is ScanStatus.COMPLETED
    assert result.total_findings >= 1
    assert all(f.location.file.endswith(".js") for f in result.findings)


def test_missing_repository_root_raises(tmp_path: Path) -> None:
    with pytest.raises(RepositoryError):
        scan_repository(tmp_path / "does_not_exist", ScanConfig.auto())


def test_analyzer_failure_raises_scan_execution_error(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "x = 1\n")
    registry = (AnalyzerEntry(_RaisingAnalyzer(), frozenset({_PY}), frozenset({"CWE-798"})),)

    with pytest.raises(ScanExecutionError) as exc_info:
        scan_repository(tmp_path, ScanConfig.auto(), registry=registry)

    assert exc_info.value.detector_name == "raising-analyzer"


def test_findings_for_unknown_language_files_are_scoped_out(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "x = 1\n")
    registry = (
        AnalyzerEntry(
            _UnknownLanguageFindingAnalyzer(), frozenset({_PY}), frozenset({"CWE-798"})
        ),
    )

    result = scan_repository(tmp_path, ScanConfig.auto(), registry=registry)

    assert result.status is ScanStatus.COMPLETED
    assert result.total_findings == 0  # the weird.unknown finding is out of scope
    assert result.analyzer_runs[0].finding_count == 0


def test_result_is_json_serializable(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "hash.py", "import hashlib\nx = hashlib.md5(data)\n")

    result = scan_repository(tmp_path, ScanConfig.auto())
    dumped = result.model_dump(mode="json")

    assert dumped["status"] == "completed"
    assert isinstance(dumped["findings"], list)
    assert dumped["total_findings"] == result.total_findings
