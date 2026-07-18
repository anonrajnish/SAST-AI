"""Unit tests for the weak-cryptography scanner (CWE-327/328)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.deterministic.weak_crypto_scanner import WeakCryptoScanner


def test_flags_python_weak_hash_and_cipher(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "h.py", "import hashlib\nx = hashlib.md5(data).hexdigest()\n")
    write_file(tmp_path / "c.py", "from Crypto.Cipher import DES\nc = DES.new(key, mode)\n")

    findings = WeakCryptoScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"h.py", "c.py"}
    cwes = {f.location.file: f.cwe for f in findings}
    assert cwes["h.py"] == "CWE-328"
    assert cwes["c.py"] == "CWE-327"
    for finding in findings:
        assert finding.detector == "weak-crypto-scanner"


def test_flags_javascript_weak_hash_and_cipher(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "h.js", 'crypto.createHash("md5");\n')
    write_file(tmp_path / "c.ts", 'crypto.createCipheriv("des-cbc", key, iv);\n')

    findings = WeakCryptoScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"h.js", "c.ts"}


def test_ignores_strong_algorithms(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "import hashlib\nx = hashlib.sha256(data).hexdigest()\n")
    write_file(tmp_path / "b.py", "from Crypto.Cipher import AES\nc = AES.new(key, mode)\n")
    write_file(tmp_path / "c.js", 'crypto.createHash("sha256");\n')
    write_file(tmp_path / "d.js", 'crypto.createCipheriv("aes-256-gcm", key, iv);\n')

    assert WeakCryptoScanner().scan(tmp_path) == []


def test_precision_anchor_ignores_names_and_comments(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.py", "md5_digest = payload  # not real md5, sha1 here\n")

    assert WeakCryptoScanner().scan(tmp_path) == []
