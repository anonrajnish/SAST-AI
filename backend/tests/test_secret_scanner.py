"""Unit tests for the hardcoded-secret scanner."""

from __future__ import annotations

from pathlib import Path

from app.services.deterministic.secret_scanner import SecretScanner


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_flags_literal_secrets_across_languages(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", 'password = "S3cr3t-Example"\n')
    _write(tmp_path / "b.ts", 'const STRIPE_SECRET_KEY = "sk_live_EXAMPLE";\n')

    findings = SecretScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.py", "b.ts"}
    for finding in findings:
        assert finding.rule_id == "hardcoded-secret-literal"
        assert finding.cwe == "CWE-798"
        assert finding.detector == "secret-scanner"


def test_ignores_environment_reads(tmp_path: Path) -> None:
    _write(tmp_path / "a.py", 'password = os.environ["DB_PASSWORD"]\n')
    _write(tmp_path / "b.ts", 'const key = import.meta.env.VITE_KEY ?? "";\n')

    assert SecretScanner().scan(tmp_path) == []


def test_findings_never_expose_secret_value(tmp_path: Path) -> None:
    secret = "sk_live_TOPSECRET_do_not_leak"
    _write(tmp_path / "a.py", f'api_key = "{secret}"\n')

    findings = SecretScanner().scan(tmp_path)

    assert len(findings) == 1
    assert secret not in findings[0].model_dump_json()  # only metadata, never the value
