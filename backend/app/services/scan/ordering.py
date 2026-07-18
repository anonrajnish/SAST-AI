"""Deterministic ordering of scan findings (Slice 4 — triage-ready shaping).

Findings are ordered by stable metadata — file path, then line range, then detector and
rule id (and CWE as a final tie-breaker) — so a :class:`~app.services.scan.results.ScanResult`
is reproducible across runs and diff-friendly for a future triage stage. Ordering only: no
deduplication and no finding id.
"""

from __future__ import annotations

from collections.abc import Iterable

from contracts import Finding


def finding_sort_key(finding: Finding) -> tuple[str, int, int, str, str, str]:
    """Stable sort key: (file, start_line, end_line, detector, rule_id, cwe).

    Missing line numbers sort before present ones (``-1``); missing string metadata sorts
    as the empty string. All components are directly comparable, so the ordering is total.
    """

    location = finding.location
    return (
        location.file,
        location.start_line if location.start_line is not None else -1,
        location.end_line if location.end_line is not None else -1,
        finding.detector or "",
        finding.rule_id or "",
        finding.cwe or "",
    )


def order_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Return ``findings`` in deterministic, reproducible order (stable; no dedup)."""

    return sorted(findings, key=finding_sort_key)
