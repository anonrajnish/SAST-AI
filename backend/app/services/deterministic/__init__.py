"""Deterministic detection layer (pattern-based analyzers).

Each analyzer is a thin :class:`~app.services.deterministic.analyzer.PatternAnalyzer` built on
the shared :func:`~app.services.deterministic.rules.scan_tree` engine, differing only by its
rule pack. :data:`~app.services.deterministic.registry.DETERMINISTIC_ANALYZERS` enumerates them
as the single source of truth.
"""

from __future__ import annotations

from .registry import ANALYZERS_BY_NAME, DETERMINISTIC_ANALYZERS

__all__ = ["ANALYZERS_BY_NAME", "DETERMINISTIC_ANALYZERS"]
