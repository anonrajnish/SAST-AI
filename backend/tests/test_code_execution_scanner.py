"""Unit tests for the dynamic-code-execution scanner (CWE-95)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.deterministic.code_execution_scanner import CodeExecutionScanner


def test_flags_python_eval_and_exec(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "def f(s):\n    return eval(s)\n")
    write_file(tmp_path / "b.py", "def g(s):\n    exec(s)\n")

    findings = CodeExecutionScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.py", "b.py"}
    for finding in findings:
        assert finding.cwe == "CWE-95"
        assert finding.detector == "code-execution-scanner"


def test_flags_js_eval_and_function_constructor(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.js", "const r = eval(input);\n")
    write_file(tmp_path / "b.ts", "const fn = new Function('return 1');\n")

    findings = CodeExecutionScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.js", "b.ts"}


def test_ignores_safe_alternatives(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "import ast\nx = ast.literal_eval(s)\n")
    write_file(tmp_path / "b.js", "const r = JSON.parse(input);\n")

    assert CodeExecutionScanner().scan(tmp_path) == []
