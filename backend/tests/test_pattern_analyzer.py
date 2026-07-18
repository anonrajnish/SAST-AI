"""Tests for the reusable PatternAnalyzer abstraction."""

from __future__ import annotations

from pathlib import Path

from app.services.deterministic.analyzer import PatternAnalyzer
from app.services.deterministic.rules import PatternRule
from contracts import Language

_RULE = PatternRule(
    id="r1",
    name="eval call",
    cwe="CWE-95",
    languages=frozenset({Language.PYTHON}),
    pattern=r"(?<![.\w])eval\s*\(",
)


def test_pattern_analyzer_uses_supplied_rules_and_name(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = eval(y)\n", encoding="utf-8")

    analyzer = PatternAnalyzer([_RULE], "custom-analyzer")
    findings = analyzer.scan(tmp_path)

    assert analyzer.detector_name == "custom-analyzer"
    assert len(findings) == 1
    assert findings[0].rule_id == "r1"
    assert findings[0].cwe == "CWE-95"
    assert findings[0].detector == "custom-analyzer"


def test_pattern_analyzer_with_no_matches(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = safe_call(y)\n", encoding="utf-8")

    assert PatternAnalyzer([_RULE], "custom-analyzer").scan(tmp_path) == []
