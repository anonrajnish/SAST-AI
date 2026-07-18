"""Registry of the deterministic pattern analyzers — the single source of truth.

Each :class:`AnalyzerEntry` pairs an analyzer instance with its authored metadata: the
language groups it applies to and the CWEs it covers. Adding an analyzer means adding one
entry here. The registry owns this metadata so :class:`PatternAnalyzer` can stay focused
solely on scanning and expose no language information of its own.

The registry knows nothing about evaluation corpora — the eval harness and its corpus ids
stay on the other side of the ``Detector`` seam.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from contracts import LanguageGroup

from .analyzer import PatternAnalyzer
from .code_execution_scanner import CodeExecutionScanner
from .reverse_tabnabbing_scanner import ReverseTabnabbingScanner
from .secret_scanner import SecretScanner
from .tls_verification_scanner import TlsVerificationScanner
from .unsafe_deserialization_scanner import UnsafeDeserializationScanner
from .weak_crypto_scanner import WeakCryptoScanner

_PYTHON_AND_WEB = frozenset({LanguageGroup.PYTHON, LanguageGroup.WEB})
_WEB_ONLY = frozenset({LanguageGroup.WEB})


@dataclass(frozen=True)
class AnalyzerEntry:
    """A deterministic analyzer plus its authored registry metadata."""

    analyzer: PatternAnalyzer
    language_groups: frozenset[LanguageGroup]
    cwes: frozenset[str]


ANALYZER_REGISTRY: tuple[AnalyzerEntry, ...] = (
    AnalyzerEntry(SecretScanner(), _PYTHON_AND_WEB, frozenset({"CWE-798"})),
    AnalyzerEntry(CodeExecutionScanner(), _PYTHON_AND_WEB, frozenset({"CWE-95"})),
    AnalyzerEntry(WeakCryptoScanner(), _PYTHON_AND_WEB, frozenset({"CWE-327", "CWE-328"})),
    AnalyzerEntry(UnsafeDeserializationScanner(), _PYTHON_AND_WEB, frozenset({"CWE-502"})),
    AnalyzerEntry(TlsVerificationScanner(), _PYTHON_AND_WEB, frozenset({"CWE-295"})),
    AnalyzerEntry(ReverseTabnabbingScanner(), _WEB_ONLY, frozenset({"CWE-1022"})),
)
"""All deterministic analyzers with their metadata, in a stable order."""

DETERMINISTIC_ANALYZERS: tuple[PatternAnalyzer, ...] = tuple(
    entry.analyzer for entry in ANALYZER_REGISTRY
)
"""All deterministic analyzer instances, in registry order."""

ANALYZERS_BY_NAME: Mapping[str, PatternAnalyzer] = {
    entry.analyzer.detector_name: entry.analyzer for entry in ANALYZER_REGISTRY
}
"""Lookup of analyzer by its ``detector_name`` (the provenance label on its findings)."""
