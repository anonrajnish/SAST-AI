"""Callable evaluation interface for the eval harness (TASK-021).

The single reusable entry point that ties the harness together: given a
dependency-injected :class:`~eval.harness.evaluation.Detector` and a corpus id, it
runs the evaluation (delegating to the orchestrator, which reuses the loader,
validator, and matcher) and — when integrity passes — computes metrics, returning
one self-contained, serializable :class:`EvaluationResult` suitable for future CLI,
REST, CI, and regression callers.

Fully dependency-injected: the caller locates the registry, labels directory, and
corpus base directory. Analyzer-agnostic — no real analyzer, no AI, and no
orchestration duplicated here (it delegates to
:func:`~eval.harness.evaluation.run_evaluation`). Integrity failure is a structured
outcome; operational faults propagate as :mod:`eval.harness.errors` types.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .evaluation import Detector, run_evaluation
from .metrics import Metrics, compute_metrics
from .models import CorpusRegistry
from .runner import EvaluationReport
from .validator import IntegrityReport


class EvaluationStatus(StrEnum):
    """Outcome status of a single-corpus evaluation."""

    EVALUATED = "evaluated"
    INTEGRITY_FAILED = "integrity_failed"


class EvaluationResult(BaseModel):
    """Self-contained, serializable result of evaluating one corpus.

    ``integrity`` is always present. On ``EVALUATED`` both ``evaluation`` and
    ``metrics`` are populated; on ``INTEGRITY_FAILED`` the detector was not run and
    both are ``None`` (``integrity`` explains why).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_id: str
    status: EvaluationStatus
    detector_name: str | None
    integrity: IntegrityReport
    evaluation: EvaluationReport | None
    metrics: Metrics | None


def evaluate_corpus(
    detector: Detector,
    corpus_id: str,
    *,
    registry: CorpusRegistry,
    labels_dir: Path,
    corpus_base_dir: Path,
    detector_name: str | None = None,
) -> EvaluationResult:
    """Evaluate ``detector`` against one corpus and return a structured result.

    Delegates orchestration to :func:`~eval.harness.evaluation.run_evaluation`
    (loader -> validator -> matcher). When integrity passes, metrics are computed
    with :func:`~eval.harness.metrics.compute_metrics`; otherwise the detector was
    not run and ``metrics``/``evaluation`` are ``None``.

    Raises the loader's :class:`~eval.harness.errors.CorpusRegistryError` for an
    unknown ``corpus_id`` and :class:`~eval.harness.errors.LabelFileError` /
    :class:`~eval.harness.errors.LabelSchemaError` for an unreadable or invalid
    label file.
    """

    corpus_eval = run_evaluation(
        detector,
        corpus_id,
        registry=registry,
        labels_dir=labels_dir,
        corpus_base_dir=corpus_base_dir,
    )

    evaluation = corpus_eval.evaluation
    metrics: Metrics | None
    if evaluation is not None:
        metrics = compute_metrics(evaluation)
        status = EvaluationStatus.EVALUATED
    else:
        metrics = None
        status = EvaluationStatus.INTEGRITY_FAILED

    return EvaluationResult(
        corpus_id=corpus_id,
        status=status,
        detector_name=detector_name,
        integrity=corpus_eval.integrity,
        evaluation=evaluation,
        metrics=metrics,
    )
