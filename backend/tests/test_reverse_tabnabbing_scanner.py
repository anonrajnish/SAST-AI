"""Unit tests for the reverse-tabnabbing scanner (CWE-1022)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.deterministic.reverse_tabnabbing_scanner import ReverseTabnabbingScanner


def test_flags_html_target_blank_without_rel(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.html", '<a href="https://x.example" target="_blank">x</a>\n')
    # mixed-case attribute name must still be flagged (case-insensitive rule)
    write_file(tmp_path / "b.html", '<a TARGET="_blank" href="https://y.example">y</a>\n')

    findings = ReverseTabnabbingScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.html", "b.html"}
    for finding in findings:
        assert finding.cwe == "CWE-1022"
        assert finding.detector == "reverse-tabnabbing-scanner"


def test_flags_javascript_window_open_blank_without_noopener(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.js", 'window.open(url, "_blank");\n')
    write_file(tmp_path / "b.ts", 'window.open(getUrl(), "_blank");\n')

    findings = ReverseTabnabbingScanner().scan(tmp_path)

    assert {f.location.file for f in findings} == {"a.js", "b.ts"}


def test_ignores_mitigated_links(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "a.html", '<a href="#" target="_blank" rel="noopener">x</a>\n')
    write_file(tmp_path / "b.html", '<a href="#" target="_blank" rel="noreferrer">y</a>\n')
    write_file(tmp_path / "c.html", '<a href="#" target="_blank" rel="noopener noreferrer">z</a>\n')
    write_file(tmp_path / "d.js", 'window.open(url, "_blank", "noopener");\n')
    write_file(tmp_path / "e.html", '<a href="/local">home</a>\n')

    assert ReverseTabnabbingScanner().scan(tmp_path) == []


def test_marker_comment_after_tag_does_not_suppress(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(
        tmp_path / "a.html",
        '<a href="#" target="_blank">x</a> <!-- missing rel=noopener -->\n',
    )

    findings = ReverseTabnabbingScanner().scan(tmp_path)

    assert len(findings) == 1
    assert findings[0].cwe == "CWE-1022"
