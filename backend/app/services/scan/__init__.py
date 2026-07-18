"""Deterministic scan pipeline over an extracted repository.

Language foundation (Slice 1): the target-language vocabulary (:class:`~contracts.LanguageGroup`,
:class:`TargetMode`, :class:`ScanConfig`) and detection (:func:`detect_language_groups`).
Resolution + selection (Slice 2): :func:`resolve_target_groups`, :func:`select_analyzers`.
Execution + aggregation (Slice 3): :func:`scan_repository` returning a :class:`ScanResult`.
"""

from __future__ import annotations

from contracts import LanguageGroup

from .detection import detect_language_groups, group_for_language
from .errors import RepositoryError, ScanError, ScanExecutionError
from .models import ScanConfig, TargetMode
from .ordering import order_findings
from .pipeline import scan_repository
from .resolution import resolve_target_groups
from .results import AnalyzerRun, ScanResult, ScanStatus
from .selection import select_analyzers

__all__ = [
    "AnalyzerRun",
    "LanguageGroup",
    "RepositoryError",
    "ScanConfig",
    "ScanError",
    "ScanExecutionError",
    "ScanResult",
    "ScanStatus",
    "TargetMode",
    "detect_language_groups",
    "group_for_language",
    "order_findings",
    "resolve_target_groups",
    "scan_repository",
    "select_analyzers",
]
