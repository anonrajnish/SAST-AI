"""Result models for the scan pipeline (Slice 3).

The structured, serializable outcome of a scan: overall status, the detected and resolved
language groups, a per-analyzer run summary, file/finding counts, and the aggregated
findings (ready for a future AI-triage stage). Deterministic; no dedup or ``finding_id`` yet.
"""

from __future__ import annotations

from enum import StrEnum

from contracts import Finding, LanguageGroup
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from .ordering import order_findings


class ScanStatus(StrEnum):
    """Overall outcome of a scan."""

    COMPLETED = "completed"
    NO_SUPPORTED_LANGUAGES = "no_supported_languages"


class AnalyzerRun(BaseModel):
    """Summary of one analyzer's contribution to the scan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    detector_name: str
    finding_count: int


class ScanResult(BaseModel):
    """The structured outcome of scanning one repository.

    On ``NO_SUPPORTED_LANGUAGES`` (AUTO detected nothing supported) the analyzer runs and
    findings are empty. ``findings`` are normalized into a deterministic, reproducible order
    (see :func:`~app.services.scan.ordering.order_findings`) so the result is stable across
    runs and diff-friendly for triage; deduplication is not performed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: ScanStatus
    detected_language_groups: frozenset[LanguageGroup]
    resolved_language_groups: frozenset[LanguageGroup]
    analyzer_runs: list[AnalyzerRun]
    files_scanned: int
    total_findings: int
    findings: list[Finding]

    @field_validator("findings")
    @classmethod
    def _order_findings(cls, findings: list[Finding]) -> list[Finding]:
        """Normalize findings into deterministic order at construction time."""

        return order_findings(findings)

    @field_serializer(
        "detected_language_groups", "resolved_language_groups", when_used="json"
    )
    def _serialize_groups(self, groups: frozenset[LanguageGroup]) -> list[str]:
        """Serialize group sets as a sorted list so the JSON result is stable across runs."""

        return sorted(group.value for group in groups)
