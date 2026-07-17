"""Hardcoded-secret scanner — the first deterministic analyzer (CWE-798).

Reuses :class:`PatternAnalyzer` unchanged and differs only by its rule pack (the
hardcoded-secret rules). Exposes the evaluation harness's ``Detector`` interface so
the harness can score it via ``evaluate_corpus``. Deterministic, read-only, no
data-flow/taint/AI. Findings carry only file, location, rule id, and CWE — never the
matched secret value.
"""

from __future__ import annotations

from .analyzer import PatternAnalyzer
from .secret_rules import SECRET_RULES


class SecretScanner(PatternAnalyzer):
    """Deterministic hardcoded-secret analyzer (satisfies the ``Detector`` protocol)."""

    def __init__(self) -> None:
        super().__init__(SECRET_RULES, "secret-scanner")
