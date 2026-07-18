"""Reusable ``Detector`` implementation for pattern-based analyzers.

Every deterministic pattern analyzer differs only by its
:class:`~app.services.deterministic.rules.PatternRule` list and a detector name;
they all reuse :class:`PatternAnalyzer`, which satisfies the evaluation harness's
``Detector`` protocol (``scan(corpus_root) -> list[Finding]``) by delegating to the
shared :func:`~app.services.deterministic.rules.scan_tree` engine.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from contracts import Finding

from .rules import PatternRule, scan_tree


class PatternAnalyzer:
    """A deterministic analyzer defined entirely by its rule list and a name."""

    def __init__(self, rules: Sequence[PatternRule], detector_name: str) -> None:
        self._rules = tuple(rules)
        self._detector_name = detector_name

    @property
    def detector_name(self) -> str:
        """The provenance label stamped on every emitted finding."""

        return self._detector_name

    def scan(self, corpus_root: Path) -> list[Finding]:
        """Return findings for every rule match under ``corpus_root``."""

        return scan_tree(corpus_root, self._rules, detector_name=self._detector_name)
