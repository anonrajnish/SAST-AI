"""Unit tests for scan-pipeline language-group detection (Slice 1)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.services.scan import LanguageGroup, detect_language_groups, group_for_language
from contracts import Language


def test_group_for_language_mapping() -> None:
    assert group_for_language(Language.PYTHON) is LanguageGroup.PYTHON
    assert group_for_language(Language.JAVASCRIPT) is LanguageGroup.WEB
    assert group_for_language(Language.TYPESCRIPT) is LanguageGroup.WEB
    assert group_for_language(Language.HTML) is LanguageGroup.WEB
    # future-roadmap languages are not supported by the MVP pipeline
    assert group_for_language(Language.JAVA) is None
    assert group_for_language(Language.GO) is None


def test_detects_python_only(tmp_path: Path, write_file: Callable[[Path, str], None]) -> None:
    write_file(tmp_path / "app.py", "x = 1\n")
    write_file(tmp_path / "pkg" / "mod.py", "y = 2\n")

    assert detect_language_groups(tmp_path) == frozenset({LanguageGroup.PYTHON})


def test_detects_web_only(tmp_path: Path, write_file: Callable[[Path, str], None]) -> None:
    write_file(tmp_path / "a.js", "const a = 1;\n")
    write_file(tmp_path / "b.ts", "const b: number = 2;\n")
    write_file(tmp_path / "index.html", "<html></html>\n")

    assert detect_language_groups(tmp_path) == frozenset({LanguageGroup.WEB})


def test_detects_both_groups(tmp_path: Path, write_file: Callable[[Path, str], None]) -> None:
    write_file(tmp_path / "server.py", "x = 1\n")
    write_file(tmp_path / "web" / "app.tsx", "const a = 1;\n")

    assert detect_language_groups(tmp_path) == frozenset(
        {LanguageGroup.PYTHON, LanguageGroup.WEB}
    )


def test_ignores_unsupported_file_types(
    tmp_path: Path, write_file: Callable[[Path, str], None]
) -> None:
    write_file(tmp_path / "README.md", "# docs\n")
    write_file(tmp_path / "notes.txt", "hello\n")
    write_file(tmp_path / "Main.java", "class Main {}\n")  # future-roadmap language

    assert detect_language_groups(tmp_path) == frozenset()


def test_empty_repository_returns_no_groups(tmp_path: Path) -> None:
    assert detect_language_groups(tmp_path) == frozenset()


def test_missing_directory_returns_no_groups(tmp_path: Path) -> None:
    assert detect_language_groups(tmp_path / "does_not_exist") == frozenset()


def test_symlinks_are_skipped(tmp_path: Path, write_file: Callable[[Path, str], None]) -> None:
    real = tmp_path / "real.py"
    write_file(real, "x = 1\n")
    link_dir = tmp_path / "links"
    link_dir.mkdir()
    (link_dir / "linked.js").symlink_to(real)  # symlink with a JS suffix must be ignored

    # only the real .py counts; the symlinked .js is skipped -> WEB not detected
    assert detect_language_groups(tmp_path) == frozenset({LanguageGroup.PYTHON})
