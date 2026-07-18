"""Registry-driven analyzer selection for the scan pipeline (Slice 2).

Selects the deterministic analyzers whose authored registry metadata applies to a set of
resolved language groups, in registry order. Analyzers and their metadata come exclusively
from the deterministic analyzer registry (the single source of truth); this module neither
executes analyzers nor aggregates findings.
"""

from __future__ import annotations

from collections.abc import Sequence

from contracts import LanguageGroup

from app.services.deterministic import ANALYZER_REGISTRY, AnalyzerEntry
from app.services.deterministic.analyzer import PatternAnalyzer


def select_analyzers(
    groups: frozenset[LanguageGroup],
    registry: Sequence[AnalyzerEntry] = ANALYZER_REGISTRY,
) -> tuple[PatternAnalyzer, ...]:
    """Return the analyzers applicable to ``groups``, in registry order.

    An analyzer is selected when its metadata language groups intersect ``groups``. Empty
    ``groups`` selects nothing. This does not execute the analyzers.
    """

    return tuple(entry.analyzer for entry in registry if entry.language_groups & groups)
