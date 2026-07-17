"""Weak cryptography analyzer (CWE-327 / CWE-328).

Third deterministic analyzer. Reuses :class:`PatternAnalyzer` unchanged and differs
from the other analyzers only by its rule pack. Deterministic, read-only, no
data-flow/taint/AI. Findings carry only file, location, rule id, and CWE.
"""

from __future__ import annotations

from .analyzer import PatternAnalyzer
from .weak_crypto_rules import WEAK_CRYPTO_RULES


class WeakCryptoScanner(PatternAnalyzer):
    """Deterministic weak-cryptography analyzer (satisfies the ``Detector`` protocol)."""

    def __init__(self) -> None:
        super().__init__(WEAK_CRYPTO_RULES, "weak-crypto-scanner")
