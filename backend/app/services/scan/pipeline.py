"""Deterministic scan-pipeline entry point (Slice 3).

Orchestrates one scan over an extracted repository root:

    detect language groups -> resolve target groups -> select analyzers (registry order)
    -> execute analyzers -> aggregate findings -> ScanResult

Analyzer behavior is unchanged; analyzers come exclusively from the deterministic registry.
Findings are aggregated in registry order and scoped to the resolved language groups (so a
MANUAL selection ignores other supported languages). No deduplication, no ``finding_id``, no
AI triage, no SARIF, no GitNexus in this slice.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from contracts import Finding, LanguageGroup

from app.services.deterministic import ANALYZER_REGISTRY, AnalyzerEntry
from app.services.deterministic.rules import language_for

from .detection import count_files_in_scope, detect_language_groups, group_for_language
from .errors import RepositoryError, ScanExecutionError
from .models import ScanConfig
from .resolution import resolve_target_groups
from .results import AnalyzerRun, ScanResult, ScanStatus
from .selection import select_analyzers


def _finding_in_scope(finding: Finding, groups: frozenset[LanguageGroup]) -> bool:
    """True when the finding's file belongs to one of the resolved language groups."""

    language = language_for(Path(finding.location.file))
    if language is None:
        return False
    group = group_for_language(language)
    return group is not None and group in groups


def scan_repository(
    repo_root: Path,
    config: ScanConfig,
    *,
    registry: Sequence[AnalyzerEntry] = ANALYZER_REGISTRY,
) -> ScanResult:
    """Scan ``repo_root`` per ``config`` and return a structured :class:`ScanResult`.

    Raises :class:`RepositoryError` if ``repo_root`` is missing or not a directory, and
    :class:`ScanExecutionError` (fail-fast) if an analyzer raises unexpectedly. When AUTO
    detection finds no supported languages, returns a ``NO_SUPPORTED_LANGUAGES`` result.
    """

    if not repo_root.is_dir():
        raise RepositoryError(f"repository root is not a directory: {repo_root}")

    detected = detect_language_groups(repo_root)
    resolved = resolve_target_groups(config, detected)

    if not resolved:
        # AUTO with nothing supported detected (MANUAL always resolves to >=1 group).
        return ScanResult(
            status=ScanStatus.NO_SUPPORTED_LANGUAGES,
            detected_language_groups=detected,
            resolved_language_groups=resolved,
            analyzer_runs=[],
            files_scanned=0,
            total_findings=0,
            findings=[],
        )

    analyzers = select_analyzers(resolved, registry)
    files_scanned = count_files_in_scope(repo_root, resolved)

    runs: list[AnalyzerRun] = []
    findings: list[Finding] = []
    for analyzer in analyzers:
        try:
            produced = analyzer.scan(repo_root)
        except Exception as exc:  # fail-fast: surface which analyzer failed
            raise ScanExecutionError(analyzer.detector_name, exc) from exc
        in_scope = [f for f in produced if _finding_in_scope(f, resolved)]
        runs.append(
            AnalyzerRun(detector_name=analyzer.detector_name, finding_count=len(in_scope))
        )
        findings.extend(in_scope)

    return ScanResult(
        status=ScanStatus.COMPLETED,
        detected_language_groups=detected,
        resolved_language_groups=resolved,
        analyzer_runs=runs,
        files_scanned=files_scanned,
        total_findings=len(findings),
        findings=findings,
    )
