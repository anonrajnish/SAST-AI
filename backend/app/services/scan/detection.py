"""Repository language-group detection for the scan pipeline (Slice 1).

Maps the shared :class:`~contracts.Language` vocabulary to the coarse
:class:`~contracts.LanguageGroup`, and detects which supported groups are
present in an extracted repository by file extension. Detection only: it does not resolve
AUTO vs MANUAL, select or execute analyzers, or read file contents for vulnerabilities.
"""

from __future__ import annotations

from pathlib import Path

from contracts import Language, LanguageGroup

from app.services.deterministic.rules import language_for

# Only the MVP-supported languages map to a group; future-roadmap languages
# (Java, C/C++, Go, C#) intentionally map to nothing and are ignored.
GROUP_BY_LANGUAGE: dict[Language, LanguageGroup] = {
    Language.PYTHON: LanguageGroup.PYTHON,
    Language.JAVASCRIPT: LanguageGroup.WEB,
    Language.TYPESCRIPT: LanguageGroup.WEB,
    Language.HTML: LanguageGroup.WEB,
}


def group_for_language(language: Language) -> LanguageGroup | None:
    """Return the MVP language group for ``language``, or ``None`` if unsupported."""

    return GROUP_BY_LANGUAGE.get(language)


def detect_language_groups(repo_root: Path) -> frozenset[LanguageGroup]:
    """Return the supported language groups present under ``repo_root``.

    Extension-based and read-only: each regular (non-symlink) file's suffix is mapped to a
    :class:`~contracts.Language` and then to a :class:`LanguageGroup`; unsupported file
    types are ignored. Returns only the groups actually detected (possibly empty). This
    performs no analyzer selection, no execution, and no vulnerability scanning.
    """

    if not repo_root.is_dir():
        return frozenset()

    groups: set[LanguageGroup] = set()
    for path in repo_root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        language = language_for(path)
        if language is None:
            continue
        group = group_for_language(language)
        if group is not None:
            groups.add(group)
    return frozenset(groups)
