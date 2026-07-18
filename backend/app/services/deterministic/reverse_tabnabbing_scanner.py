"""Reverse tabnabbing analyzer (CWE-1022).

Sixth and final MVP deterministic analyzer. Reuses :class:`PatternAnalyzer` unchanged and
differs from the other analyzers only by its rule pack. Deterministic, read-only, no
data-flow/taint/AI. Findings carry only file, location, rule id, and CWE.
"""

from __future__ import annotations

from .analyzer import PatternAnalyzer
from .reverse_tabnabbing_rules import REVERSE_TABNABBING_RULES


class ReverseTabnabbingScanner(PatternAnalyzer):
    """Deterministic reverse-tabnabbing analyzer (satisfies the ``Detector`` protocol)."""

    def __init__(self) -> None:
        super().__init__(REVERSE_TABNABBING_RULES, "reverse-tabnabbing-scanner")
