"""Evaluation-result contract and label-to-finding matching for the eval runner.

This is the scoring core of the evaluation runner (TASK-020b): it defines what a
detector reports (:class:`Finding`) and deterministically classifies each
ground-truth label against those findings as a true positive, false positive, or
false negative. It is **read-only and analyzer-agnostic** — it neither runs nor
imports any detector or AI, and it does not compute precision/recall/F1 (that is
the metrics reporter, :mod:`~eval.harness.metrics`). Detector orchestration over a
corpus tree lives in :mod:`~eval.harness.evaluation`.

True negatives are intentionally **not modelled**: they are not well-defined for
SAST evaluation and are not required for the MVP metrics (precision, recall, F1).
A ``safe`` label with no matching finding therefore produces no outcome at all.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from contracts import Finding, SourceLocation

from .models import LabelSet, Verdict


class MatchOutcome(StrEnum):
    """Classification of a ground-truth label against detector findings.

    True negatives are out of scope for the MVP harness (see the module docstring).
    """

    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"


class LabelOutcome(BaseModel):
    """The classification of one ground-truth label against the findings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label_id: str
    expected: Verdict
    outcome: MatchOutcome
    matched_finding_count: int


class EvaluationReport(BaseModel):
    """Per-label outcomes for one corpus, plus findings that matched no label.

    Carries raw confusion counts only; aggregation into precision/recall/F1 is
    TASK-020c. ``unmatched_findings`` are findings that overlapped no label — a
    runner-level false-positive signal whose metric treatment TASK-020c decides.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_id: str
    label_outcomes: list[LabelOutcome]
    unmatched_findings: list[Finding]

    def _count(self, outcome: MatchOutcome) -> int:
        return sum(1 for item in self.label_outcomes if item.outcome is outcome)

    @property
    def n_true_positive(self) -> int:
        """Number of vulnerable labels a finding correctly matched."""

        return self._count(MatchOutcome.TRUE_POSITIVE)

    @property
    def n_false_positive(self) -> int:
        """Number of safe labels a finding incorrectly matched."""

        return self._count(MatchOutcome.FALSE_POSITIVE)

    @property
    def n_false_negative(self) -> int:
        """Number of vulnerable labels no finding matched."""

        return self._count(MatchOutcome.FALSE_NEGATIVE)


def _line_span(location: SourceLocation) -> tuple[int, int] | None:
    """Return the inclusive ``(start, end)`` line span, or ``None`` for whole-file."""

    if location.start_line is None:
        return None
    end = location.end_line if location.end_line is not None else location.start_line
    return (location.start_line, end)


def _locations_overlap(finding_loc: SourceLocation, label_loc: SourceLocation) -> bool:
    """True when both locations share a file and their line ranges overlap.

    A location without a ``start_line`` is treated as covering the whole file.
    """

    if finding_loc.file != label_loc.file:
        return False
    finding_span = _line_span(finding_loc)
    label_span = _line_span(label_loc)
    if finding_span is None or label_span is None:
        return True
    return finding_span[0] <= label_span[1] and label_span[0] <= finding_span[1]


def match_findings_to_labels(
    label_set: LabelSet, findings: Iterable[Finding]
) -> EvaluationReport:
    """Classify each label in ``label_set`` against ``findings`` (TP / FP / FN).

    Deterministic and location-based: a finding matches a label when they share a
    file and their line ranges overlap. Vulnerable labels yield a true positive
    (matched) or false negative (unmatched); safe labels yield a false positive
    (matched) or **no outcome** (unmatched — true negatives are out of scope).
    Findings that match no label are returned in ``unmatched_findings``.
    """

    findings_list = list(findings)
    matched_finding_indices: set[int] = set()
    label_outcomes: list[LabelOutcome] = []

    for label in label_set.labels:
        matched = [
            index
            for index, finding in enumerate(findings_list)
            if _locations_overlap(finding.location, label.location)
        ]
        matched_finding_indices.update(matched)
        count = len(matched)

        if label.verdict is Verdict.VULNERABLE:
            outcome = MatchOutcome.TRUE_POSITIVE if count else MatchOutcome.FALSE_NEGATIVE
        elif count:
            outcome = MatchOutcome.FALSE_POSITIVE
        else:
            continue  # safe label, not flagged -> no outcome (true negative out of scope)

        label_outcomes.append(
            LabelOutcome(
                label_id=label.label_id,
                expected=label.verdict,
                outcome=outcome,
                matched_finding_count=count,
            )
        )

    unmatched_findings = [
        finding
        for index, finding in enumerate(findings_list)
        if index not in matched_finding_indices
    ]
    return EvaluationReport(
        corpus_id=label_set.corpus_id,
        label_outcomes=label_outcomes,
        unmatched_findings=unmatched_findings,
    )
