"""Reusable foundation for deterministic, pattern-based analyzers.

Defines a single-line pattern rule (:class:`PatternRule`) and a generic,
rule-agnostic scanning engine (:func:`scan_tree`) that walks a source tree,
applies regex rules per line, and emits harness-ready
:class:`~eval.harness.runner.Finding` objects. This is the shared foundation the
first analyzer (the hardcoded-secret scanner) and future pattern-based analyzers
build on by supplying their own rules.

No data-flow, taint, interprocedural analysis, or rule engine here (YAML rulepacks
remain deferred, TASK-241). Corpus files are read as text and never imported or
executed (AI_DEVELOPMENT_GUIDE §8); findings carry only location metadata — never
matched source text.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from eval.harness.models import CweStr, Language, SourceLocation
from eval.harness.runner import Finding
from pydantic import BaseModel, ConfigDict

_MAX_FILE_BYTES = 1_000_000

LANGUAGE_BY_SUFFIX: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".html": Language.HTML,
    ".htm": Language.HTML,
}


class PatternRule(BaseModel):
    """A single-line regex rule scoped to a set of languages.

    ``pattern`` is matched against each line with :func:`re.search`; a match yields
    one finding at that line. Patterns must be linear (no catastrophic backtracking).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    cwe: CweStr
    languages: frozenset[Language]
    pattern: str


def language_for(path: Path) -> Language | None:
    """Return the language for ``path`` by file extension, or ``None`` if unsupported."""

    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower())


def _read_text(path: Path) -> str | None:
    """Read ``path`` as UTF-8 text, or ``None`` if unreadable, binary, or oversized."""

    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def scan_tree(
    corpus_root: Path, rules: Iterable[PatternRule], *, detector_name: str
) -> list[Finding]:
    """Apply ``rules`` line-by-line to every supported file under ``corpus_root``.

    Read-only and deterministic: files are read as text (never executed), symlinks
    are skipped and paths resolving outside the root are ignored, and findings are
    returned in a stable (file, line, rule) order. Each finding carries only its
    location, rule id, and CWE — never the matched text.
    """

    root = corpus_root.resolve()
    compiled = [(re.compile(rule.pattern), rule) for rule in rules]
    findings: list[Finding] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if root != path.resolve() and root not in path.resolve().parents:
            continue
        language = language_for(path)
        if language is None:
            continue
        text = _read_text(path)
        if text is None:
            continue
        relative = path.relative_to(root).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            for regex, rule in compiled:
                if language in rule.languages and regex.search(line):
                    findings.append(
                        Finding(
                            location=SourceLocation(
                                file=relative,
                                start_line=line_number,
                                end_line=line_number,
                            ),
                            cwe=rule.cwe,
                            rule_id=rule.id,
                            detector=detector_name,
                        )
                    )
    return findings
