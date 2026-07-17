"""Integration: score the weak-cryptography scanner through the evaluation harness."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.deterministic.weak_crypto_scanner import WeakCryptoScanner
from eval.harness.evaluation import Detector
from eval.harness.interface import EvaluationStatus, evaluate_corpus
from eval.harness.loader import load_corpus_registry

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY = _EVAL / "corpus_registry.json"
_LABELS = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"


def test_weak_crypto_scanner_satisfies_detector_protocol() -> None:
    detector: Detector = WeakCryptoScanner()  # structural conformance
    assert callable(detector.scan)


@pytest.mark.parametrize("corpus_id", ["weak_crypto_py", "weak_crypto_js"])
def test_weak_crypto_scored_by_harness(corpus_id: str) -> None:
    registry = load_corpus_registry(_REGISTRY)

    result = evaluate_corpus(
        WeakCryptoScanner(),
        corpus_id,
        registry=registry,
        labels_dir=_LABELS,
        corpus_base_dir=_COMMITTED,
        detector_name="weak-crypto-scanner",
    )

    assert result.status is EvaluationStatus.EVALUATED
    assert result.metrics is not None
    assert result.metrics.true_positives == 2
    assert result.metrics.false_positives == 0
    assert result.metrics.false_negatives == 0
    assert result.metrics.precision == pytest.approx(1.0)
    assert result.metrics.recall == pytest.approx(1.0)
