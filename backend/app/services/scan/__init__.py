"""Deterministic scan pipeline over an extracted repository.

Language foundation (Slice 1): the target-language vocabulary (:class:`~contracts.LanguageGroup`,
:class:`TargetMode`, :class:`ScanConfig`) and detection (:func:`detect_language_groups`).
Resolution + selection (Slice 2): :func:`resolve_target_groups` (AUTO/MANUAL) and
:func:`select_analyzers` (registry-driven). Execution and aggregation arrive in later slices.
"""

from __future__ import annotations

from contracts import LanguageGroup

from .detection import detect_language_groups, group_for_language
from .models import ScanConfig, TargetMode
from .resolution import resolve_target_groups
from .selection import select_analyzers

__all__ = [
    "LanguageGroup",
    "ScanConfig",
    "TargetMode",
    "detect_language_groups",
    "group_for_language",
    "resolve_target_groups",
    "select_analyzers",
]
