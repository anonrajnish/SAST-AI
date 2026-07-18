"""Integration: score every deterministic analyzer through the evaluation harness.

Drives the analyzers from the single-source-of-truth registry
(:data:`app.services.deterministic.DETERMINISTIC_ANALYZERS`) and asserts the
expected precision/recall on each analyzer's own corpus (plus the cross-corpus
recall checks the individual scanners used to make). Also exercises the interface's
``detector_name`` default: ``evaluate_corpus`` is called *without* ``detector_name``,
so the result must pick it up from the analyzer itself.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.deterministic import ANALYZERS_BY_NAME, DETERMINISTIC_ANALYZERS
from contracts import Detector
from eval.harness.interface import EvaluationStatus, evaluate_corpus
from eval.harness.loader import load_corpus_registry

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY = _EVAL / "corpus_registry.json"
_LABELS = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"

# (detector_name, corpus_id, tp, fp, fn, precision, recall)
_CASES: list[tuple[str, str, int, int, int, float, float]] = [
    ("secret-scanner", "web_curated_ts", 1, 0, 1, 1.0, 0.5),
    ("secret-scanner", "project_curated", 2, 0, 8, 1.0, 0.2),
    ("code-execution-scanner", "code_exec_py", 2, 0, 0, 1.0, 1.0),
    ("code-execution-scanner", "web_curated_js", 1, 0, 1, 1.0, 0.5),
    ("weak-crypto-scanner", "weak_crypto_py", 2, 0, 0, 1.0, 1.0),
    ("weak-crypto-scanner", "weak_crypto_js", 2, 0, 0, 1.0, 1.0),
    ("unsafe-deserialization-scanner", "unsafe_deserialization_py", 2, 0, 0, 1.0, 1.0),
    ("unsafe-deserialization-scanner", "unsafe_deserialization_js", 2, 0, 0, 1.0, 1.0),
    ("tls-verification-scanner", "tls_verification_py", 2, 0, 0, 1.0, 1.0),
    ("tls-verification-scanner", "tls_verification_js", 2, 0, 0, 1.0, 1.0),
    ("reverse-tabnabbing-scanner", "reverse_tabnabbing_html", 2, 0, 0, 1.0, 1.0),
    ("reverse-tabnabbing-scanner", "reverse_tabnabbing_js", 2, 0, 0, 1.0, 1.0),
]


def test_registry_analyzers_are_unique_and_protocol_conformant() -> None:
    names = [analyzer.detector_name for analyzer in DETERMINISTIC_ANALYZERS]
    assert len(names) == len(set(names))  # no duplicate detector names
    assert set(names) == set(ANALYZERS_BY_NAME)
    for analyzer in DETERMINISTIC_ANALYZERS:
        detector: Detector = analyzer  # structural conformance to the Detector seam
        assert callable(detector.scan)
        assert analyzer.detector_name


@pytest.mark.parametrize(
    ("detector_name", "corpus_id", "tp", "fp", "fn", "precision", "recall"),
    _CASES,
    ids=[f"{name}:{corpus}" for name, corpus, *_ in _CASES],
)
def test_analyzer_scored_by_harness(
    detector_name: str,
    corpus_id: str,
    tp: int,
    fp: int,
    fn: int,
    precision: float,
    recall: float,
) -> None:
    registry = load_corpus_registry(_REGISTRY)
    analyzer = ANALYZERS_BY_NAME[detector_name]

    result = evaluate_corpus(  # no detector_name -> taken from the analyzer (S1)
        analyzer,
        corpus_id,
        registry=registry,
        labels_dir=_LABELS,
        corpus_base_dir=_COMMITTED,
    )

    assert result.status is EvaluationStatus.EVALUATED
    assert result.detector_name == detector_name  # defaulted from the analyzer
    assert result.metrics is not None
    assert result.metrics.true_positives == tp
    assert result.metrics.false_positives == fp
    assert result.metrics.false_negatives == fn
    assert result.metrics.precision == pytest.approx(precision)
    assert result.metrics.recall == pytest.approx(recall)
