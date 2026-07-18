"""Unit tests for the disabled-TLS-verification scanner (CWE-295)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.deterministic.tls_verification_scanner import TlsVerificationScanner


def test_flags_python_verify_false_and_unverified_context(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "r.py", "import requests\nrequests.get(url, verify=False)\n")
    write_file(tmp_path / "s.py", "session.verify = False\n")
    write_file(tmp_path / "c.py", "import ssl\nctx = ssl._create_unverified_context()\n")

    findings = TlsVerificationScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"r.py", "s.py", "c.py"}
    for finding in findings:
        assert finding.cwe == "CWE-295"
        assert finding.detector == "tls-verification-scanner"


def test_flags_javascript_reject_unauthorized_false(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.js", "const agent = new https.Agent({ rejectUnauthorized: false });\n")
    write_file(tmp_path / "b.ts", "const opts = { rejectUnauthorized: false };\n")

    findings = TlsVerificationScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.js", "b.ts"}


def test_ignores_enabled_verification(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "import requests\nrequests.get(url, verify=True)\n")
    write_file(tmp_path / "b.py", "import ssl\nctx = ssl.create_default_context()\n")
    write_file(tmp_path / "c.js", "const agent = new https.Agent({ rejectUnauthorized: true });\n")

    assert TlsVerificationScanner().scan(tmp_path) == []


def test_ignores_comparison_and_identifier_substring(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(
        tmp_path / "a.py",
        "if verify == False:\n    handle()\nmyverify=False\n",
    )

    assert TlsVerificationScanner().scan(tmp_path) == []
