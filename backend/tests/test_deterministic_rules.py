"""Unit tests for the deterministic pattern-scanning foundation."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.deterministic import rules
from app.services.deterministic.rules import (
    LANGUAGE_BY_SUFFIX,
    PatternRule,
    language_for,
    scan_tree,
)
from eval.harness.models import Language

_RULE = PatternRule(
    id="test-token",
    name="token literal",
    cwe="CWE-798",
    languages=frozenset({Language.PYTHON, Language.TYPESCRIPT}),
    pattern=r"(?i)token\s*=\s*[\"']",
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_language_for_known_and_unknown() -> None:
    assert language_for(Path("a.py")) is Language.PYTHON
    assert language_for(Path("a.TS")) is Language.TYPESCRIPT  # case-insensitive
    assert language_for(Path("a.txt")) is None
    assert set(LANGUAGE_BY_SUFFIX).issuperset({".py", ".js", ".ts", ".html"})


def test_scan_tree_matches_and_reports_location(tmp_path: Path) -> None:
    _write(tmp_path / "pkg" / "a.py", "x = 1\ntoken = 'abc'\n")
    findings = scan_tree(tmp_path, [_RULE], detector_name="d")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.location.file == "pkg/a.py"
    assert finding.location.start_line == 2
    assert finding.rule_id == "test-token"
    assert finding.cwe == "CWE-798"
    assert finding.detector == "d"


def test_scan_tree_ignores_env_reads(tmp_path: Path) -> None:
    _write(tmp_path / "safe.py", "token = os.environ['TOKEN']\n")
    assert scan_tree(tmp_path, [_RULE], detector_name="d") == []


def test_scan_tree_skips_unsupported_extension(tmp_path: Path) -> None:
    _write(tmp_path / "notes.txt", "token = 'abc'\n")
    assert scan_tree(tmp_path, [_RULE], detector_name="d") == []


def test_scan_tree_respects_rule_language_scope(tmp_path: Path) -> None:
    _write(tmp_path / "a.js", "token = 'abc'\n")  # rule scoped to python/typescript
    assert scan_tree(tmp_path, [_RULE], detector_name="d") == []


def test_scan_tree_skips_oversized_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rules, "_MAX_FILE_BYTES", 5)
    _write(tmp_path / "big.py", "token = 'abc'\n")
    assert scan_tree(tmp_path, [_RULE], detector_name="d") == []


def test_scan_tree_skips_binary_file(tmp_path: Path) -> None:
    (tmp_path / "bin.py").write_bytes(b"\xff\xfe\x00token = 'abc'")
    assert scan_tree(tmp_path, [_RULE], detector_name="d") == []


def test_scan_tree_skips_symlinks(tmp_path: Path) -> None:
    real = tmp_path / "real.py"
    real.write_text("token = 'abc'\n", encoding="utf-8")
    (tmp_path / "link.py").symlink_to(real)
    findings = scan_tree(tmp_path, [_RULE], detector_name="d")
    assert [f.location.file for f in findings] == ["real.py"]  # symlink skipped


def test_scan_tree_is_deterministic(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", "token = 'a'\n")
    _write(tmp_path / "b.py", "token = 'b'\n")
    first = [f.location.file for f in scan_tree(tmp_path, [_RULE], detector_name="d")]
    second = [f.location.file for f in scan_tree(tmp_path, [_RULE], detector_name="d")]
    assert first == second == ["a.py", "b.py"]
