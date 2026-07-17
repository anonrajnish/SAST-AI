"""Integration: score the secret scanner through the evaluation harness."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.deterministic.secret_scanner import SecretScanner
from eval.harness.evaluation import Detector
from eval.harness.interface import EvaluationStatus, evaluate_corpus
from eval.harness.loader import load_corpus_registry

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY = _EVAL / "corpus_registry.json"
_LABELS = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"


def test_secret_scanner_satisfies_detector_protocol() -> None:
    detector: Detector = SecretScanner()  # structural conformance to the Detector seam
    assert callable(detector.scan)


@pytest.mark.parametrize(
    ("corpus_id", "tp", "fp", "fn", "precision", "recall"),
    [
        ("web_curated_ts", 1, 0, 1, 1.0, 0.5),
        ("project_curated", 2, 0, 8, 1.0, 0.2),
    ],
)
def test_secret_scanner_scored_by_harness(
    corpus_id: str, tp: int, fp: int, fn: int, precision: float, recall: float
) -> None:
    registry = load_corpus_registry(_REGISTRY)

    result = evaluate_corpus(
        SecretScanner(),
        corpus_id,
        registry=registry,
        labels_dir=_LABELS,
        corpus_base_dir=_COMMITTED,
        detector_name="secret-scanner",
    )

    assert result.status is EvaluationStatus.EVALUATED
    assert result.metrics is not None
    assert result.metrics.true_positives == tp
    assert result.metrics.false_positives == fp
    assert result.metrics.false_negatives == fn
    assert result.metrics.precision == pytest.approx(precision)
    assert result.metrics.recall == pytest.approx(recall)
