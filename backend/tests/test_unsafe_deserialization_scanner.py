"""Unit tests for the unsafe-deserialization scanner (CWE-502)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.deterministic.unsafe_deserialization_scanner import (
    UnsafeDeserializationScanner,
)


def test_flags_python_pickle_and_yaml_load(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "p.py", "import pickle\nx = pickle.loads(data)\n")
    write_file(tmp_path / "y.py", "import yaml\nx = yaml.load(stream)\n")

    findings = UnsafeDeserializationScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"p.py", "y.py"}
    for finding in findings:
        assert finding.cwe == "CWE-502"
        assert finding.detector == "unsafe-deserialization-scanner"


def test_flags_javascript_unserialize(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.js", "const s = require('node-serialize');\nx = s.unserialize(p);\n")
    write_file(tmp_path / "b.ts", "const obj = unserialize(payload);\n")

    findings = UnsafeDeserializationScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.js", "b.ts"}


def test_ignores_safe_deserialization(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "import json\nx = json.loads(data)\n")
    write_file(tmp_path / "b.py", "import yaml\nx = yaml.safe_load(stream)\n")
    write_file(tmp_path / "c.js", "const obj = JSON.parse(payload);\n")

    assert UnsafeDeserializationScanner().scan(tmp_path) == []


def test_precision_anchor_ignores_qualified_and_comments(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(
        tmp_path / "a.py",
        "result = obj.pickle.loads(payload)  # attribute, not the pickle module\n"
        "value = data  # yaml.load referenced only in a comment\n",
    )

    assert UnsafeDeserializationScanner().scan(tmp_path) == []
