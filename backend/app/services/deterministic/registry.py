"""Registry of the deterministic pattern analyzers — the single source of truth.

Every deterministic analyzer is a :class:`~app.services.deterministic.analyzer.PatternAnalyzer`
that differs only by its rule pack and detector name. This module enumerates the shipped
analyzers once, so callers (the future scan pipeline, tests, tooling) discover them from one
place instead of importing each scanner ad hoc. Adding an analyzer means adding one entry here.

The registry holds analyzer *instances* (they are cheap and stateless). It knows nothing about
evaluation corpora — the eval harness and its corpus ids stay on the other side of the
``Detector`` seam.
"""

from __future__ import annotations

from collections.abc import Mapping

from .analyzer import PatternAnalyzer
from .code_execution_scanner import CodeExecutionScanner
from .reverse_tabnabbing_scanner import ReverseTabnabbingScanner
from .secret_scanner import SecretScanner
from .tls_verification_scanner import TlsVerificationScanner
from .unsafe_deserialization_scanner import UnsafeDeserializationScanner
from .weak_crypto_scanner import WeakCryptoScanner

DETERMINISTIC_ANALYZERS: tuple[PatternAnalyzer, ...] = (
    SecretScanner(),
    CodeExecutionScanner(),
    WeakCryptoScanner(),
    UnsafeDeserializationScanner(),
    TlsVerificationScanner(),
    ReverseTabnabbingScanner(),
)
"""All deterministic analyzers, in a stable order."""

ANALYZERS_BY_NAME: Mapping[str, PatternAnalyzer] = {
    analyzer.detector_name: analyzer for analyzer in DETERMINISTIC_ANALYZERS
}
"""Lookup of analyzer by its ``detector_name`` (the provenance label on its findings)."""
