"""Unit tests for the hardcoded-secret scanner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.deterministic.secret_scanner import SecretScanner


def test_flags_literal_secrets_across_languages(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", 'password = "S3cr3t-Example"\n')
    write_file(tmp_path / "b.ts", 'const STRIPE_SECRET_KEY = "sk_live_EXAMPLE";\n')

    findings = SecretScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.py", "b.ts"}
    for finding in findings:
        assert finding.rule_id == "hardcoded-secret-literal"
        assert finding.cwe == "CWE-798"
        assert finding.detector == "secret-scanner"


def test_ignores_environment_reads(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", 'password = os.environ["DB_PASSWORD"]\n')
    write_file(tmp_path / "b.ts", 'const key = import.meta.env.VITE_KEY ?? "";\n')

    assert SecretScanner().scan(tmp_path) == []


def test_findings_never_expose_secret_value(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    secret = "sk_live_TOPSECRET_do_not_leak"
    write_file(tmp_path / "a.py", f'api_key = "{secret}"\n')

    findings = SecretScanner().scan(tmp_path)

    assert len(findings) == 1
    assert secret not in findings[0].model_dump_json()  # only metadata, never the value
