"""Evaluation metrics for the eval harness (TASK-020c).

Computes precision, recall, and F1 from an :class:`~eval.harness.runner.EvaluationReport`'s
true-positive / false-positive / false-negative counts and returns an immutable
:class:`Metrics` result. Pure and analyzer-agnostic: it performs no scanning, corpus
loading, orchestration, AI, or CLI/API work — it reads integer counts only.

True negatives are out of scope (since TASK-020b, Slice 1). Unmatched findings are excluded
from precision (label-centric methodology) and remain inspectable on the report.
Aggregation across reports (micro/macro/weighted) is deliberately deferred to a later slice.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .runner import EvaluationReport


def _ratio(numerator: int, denominator: int) -> float:
    """Safe ratio: 0.0 when the denominator is 0 (documented convention)."""

    return numerator / denominator if denominator else 0.0


class Metrics(BaseModel):
    """Immutable precision/recall/F1 result for one evaluation.

    The counts and the derived precision/recall/F1 are computed once (by
    :func:`compute_metrics`) and stored. Precision = TP/(TP+FP), Recall =
    TP/(TP+FN), F1 = 2*TP/(2*TP+FP+FN); each derived value is 0.0 when its
    denominator is 0.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float


def compute_metrics(report: EvaluationReport) -> Metrics:
    """Compute :class:`Metrics` from a report's TP/FP/FN counts."""

    tp = report.n_true_positive
    fp = report.n_false_positive
    fn = report.n_false_negative
    return Metrics(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=_ratio(tp, tp + fp),
        recall=_ratio(tp, tp + fn),
        f1=_ratio(2 * tp, 2 * tp + fp + fn),
    )
