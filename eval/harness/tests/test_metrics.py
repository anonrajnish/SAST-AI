"""Unit tests for the evaluation metrics layer (TASK-020c)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ..evaluation import run_evaluation
from ..loader import load_corpus_registry
from ..metrics import Metrics, compute_metrics
from ..models import SourceLocation, Verdict
from ..runner import EvaluationReport, Finding, LabelOutcome, MatchOutcome

_REPO_ROOT = Path(__file__).parents[3]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY_PATH = _EVAL / "corpus_registry.json"
_LABELS_DIR = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"


def _report(tp: int, fp: int, fn: int) -> EvaluationReport:
    outcomes: list[LabelOutcome] = []
    for i in range(tp):
        outcomes.append(
            LabelOutcome(
                label_id=f"tp{i}",
                expected=Verdict.VULNERABLE,
                outcome=MatchOutcome.TRUE_POSITIVE,
                matched_finding_count=1,
            )
        )
    for i in range(fp):
        outcomes.append(
            LabelOutcome(
                label_id=f"fp{i}",
                expected=Verdict.SAFE,
                outcome=MatchOutcome.FALSE_POSITIVE,
                matched_finding_count=1,
            )
        )
    for i in range(fn):
        outcomes.append(
            LabelOutcome(
                label_id=f"fn{i}",
                expected=Verdict.VULNERABLE,
                outcome=MatchOutcome.FALSE_NEGATIVE,
                matched_finding_count=0,
            )
        )
    return EvaluationReport(corpus_id="c", label_outcomes=outcomes, unmatched_findings=[])


def test_counts_pass_through() -> None:
    metrics = compute_metrics(_report(3, 1, 2))
    assert metrics.true_positives == 3
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 2


def test_worked_example() -> None:
    metrics = compute_metrics(_report(3, 1, 2))
    assert metrics.precision == pytest.approx(0.75)  # 3 / (3 + 1)
    assert metrics.recall == pytest.approx(0.6)  # 3 / (3 + 2)
    assert metrics.f1 == pytest.approx(2 / 3)  # 6 / (6 + 1 + 2)


def test_perfect_scores() -> None:
    metrics = compute_metrics(_report(5, 0, 0))
    assert metrics.precision == pytest.approx(1.0)
    assert metrics.recall == pytest.approx(1.0)
    assert metrics.f1 == pytest.approx(1.0)


def test_no_predictions_is_zero_not_error() -> None:
    metrics = compute_metrics(_report(0, 0, 4))
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0


def test_only_false_positives_is_zero() -> None:
    metrics = compute_metrics(_report(0, 2, 0))
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0


def test_empty_report_has_no_zero_division() -> None:
    metrics = compute_metrics(_report(0, 0, 0))
    assert metrics.true_positives == 0
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0


def test_metrics_is_frozen() -> None:
    metrics = compute_metrics(_report(1, 0, 0))
    with pytest.raises(ValidationError):
        metrics.precision = 0.0


def test_metrics_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        Metrics.model_validate(
            {
                "true_positives": 1,
                "false_positives": 0,
                "false_negatives": 0,
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
                "unexpected": "x",
            }
        )


class _FixedDetector:
    def __init__(self, findings: list[Finding]) -> None:
        self._findings = findings

    def scan(self, corpus_root: Path) -> list[Finding]:
        return list(self._findings)


def test_metrics_from_real_pipeline() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    detector = _FixedDetector(
        [
            Finding(location=SourceLocation(file="dom_xss/vulnerable.js", start_line=5, end_line=5)),
            Finding(location=SourceLocation(file="dom_xss/secure.js", start_line=5, end_line=5)),
        ]
    )
    result = run_evaluation(
        detector,
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )
    assert result.evaluation is not None

    metrics = compute_metrics(result.evaluation)
    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision == pytest.approx(0.5)
    assert metrics.recall == pytest.approx(0.5)
    assert metrics.f1 == pytest.approx(0.5)
