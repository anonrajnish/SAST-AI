"""Unsafe deserialization analyzer (CWE-502).

Fourth deterministic analyzer. Reuses :class:`PatternAnalyzer` unchanged and differs
from the other analyzers only by its rule pack. Deterministic, read-only, no
data-flow/taint/AI. Findings carry only file, location, rule id, and CWE.
"""

from __future__ import annotations

from .analyzer import PatternAnalyzer
from .unsafe_deserialization_rules import UNSAFE_DESERIALIZATION_RULES


class UnsafeDeserializationScanner(PatternAnalyzer):
    """Deterministic unsafe-deserialization analyzer (satisfies the ``Detector`` protocol)."""

    def __init__(self) -> None:
        super().__init__(UNSAFE_DESERIALIZATION_RULES, "unsafe-deserialization-scanner")
