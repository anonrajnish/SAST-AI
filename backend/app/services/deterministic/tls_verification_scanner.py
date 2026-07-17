"""TLS certificate verification disabled analyzer (CWE-295).

Fifth deterministic analyzer. Reuses :class:`PatternAnalyzer` unchanged and differs
from the other analyzers only by its rule pack. Deterministic, read-only, no
data-flow/taint/AI. Findings carry only file, location, rule id, and CWE.
"""

from __future__ import annotations

from .analyzer import PatternAnalyzer
from .tls_verification_rules import TLS_VERIFICATION_RULES


class TlsVerificationScanner(PatternAnalyzer):
    """Deterministic disabled-TLS-verification analyzer (satisfies the ``Detector`` protocol)."""

    def __init__(self) -> None:
        super().__init__(TLS_VERIFICATION_RULES, "tls-verification-scanner")
