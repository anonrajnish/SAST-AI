"""Integration: score the code-execution scanner through the evaluation harness."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.deterministic.code_execution_scanner import CodeExecutionScanner
from eval.harness.evaluation import Detector
from eval.harness.interface import EvaluationStatus, evaluate_corpus
from eval.harness.loader import load_corpus_registry

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY = _EVAL / "corpus_registry.json"
_LABELS = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"


def test_code_execution_scanner_satisfies_detector_protocol() -> None:
    detector: Detector = CodeExecutionScanner()  # structural conformance
    assert callable(detector.scan)


@pytest.mark.parametrize(
    ("corpus_id", "tp", "fp", "fn", "precision", "recall"),
    [
        ("code_exec_py", 2, 0, 0, 1.0, 1.0),
        ("web_curated_js", 1, 0, 1, 1.0, 0.5),
    ],
)
def test_code_execution_scored_by_harness(
    corpus_id: str, tp: int, fp: int, fn: int, precision: float, recall: float
) -> None:
    registry = load_corpus_registry(_REGISTRY)

    result = evaluate_corpus(
        CodeExecutionScanner(),
        corpus_id,
        registry=registry,
        labels_dir=_LABELS,
        corpus_base_dir=_COMMITTED,
        detector_name="code-execution-scanner",
    )

    assert result.status is EvaluationStatus.EVALUATED
    assert result.metrics is not None
    assert result.metrics.true_positives == tp
    assert result.metrics.false_positives == fp
    assert result.metrics.false_negatives == fn
    assert result.metrics.precision == pytest.approx(precision)
    assert result.metrics.recall == pytest.approx(recall)
