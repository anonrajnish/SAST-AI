"""Tests for the callable evaluation interface (TASK-021)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ..errors import CorpusRegistryError
from ..interface import EvaluationResult, EvaluationStatus, evaluate_corpus
from ..loader import load_corpus_registry
from ..models import SourceLocation
from ..runner import Finding

_REPO_ROOT = Path(__file__).parents[3]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY_PATH = _EVAL / "corpus_registry.json"
_LABELS_DIR = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"


class _FixedDetector:
    def __init__(self, findings: list[Finding]) -> None:
        self._findings = findings

    def scan(self, corpus_root: Path) -> list[Finding]:
        return list(self._findings)


class _RaisingDetector:
    def scan(self, corpus_root: Path) -> list[Finding]:
        raise AssertionError("detector must not run when integrity fails")


def _finding(file: str, line: int) -> Finding:
    return Finding(location=SourceLocation(file=file, start_line=line, end_line=line))


def test_evaluate_corpus_happy_path() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    detector = _FixedDetector(
        [_finding("dom_xss/vulnerable.js", 5), _finding("dom_xss/secure.js", 5)]
    )

    result = evaluate_corpus(
        detector,
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
        detector_name="fixed-fake",
    )

    assert result.status is EvaluationStatus.EVALUATED
    assert result.corpus_id == "web_curated_js"
    assert result.detector_name == "fixed-fake"
    assert result.integrity.ok
    assert result.evaluation is not None
    assert result.metrics is not None
    assert result.metrics.true_positives == 1
    assert result.metrics.false_positives == 1
    assert result.metrics.false_negatives == 1
    assert result.metrics.precision == pytest.approx(0.5)
    assert result.metrics.recall == pytest.approx(0.5)
    assert result.metrics.f1 == pytest.approx(0.5)


def test_evaluate_corpus_detector_name_defaults_to_none() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)

    result = evaluate_corpus(
        _FixedDetector([]),
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )

    assert result.detector_name is None
    assert result.status is EvaluationStatus.EVALUATED
    assert result.metrics is not None
    assert result.metrics.false_negatives == 2  # both vulnerable labels missed


def test_evaluate_corpus_unknown_corpus_raises() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    with pytest.raises(CorpusRegistryError):
        evaluate_corpus(
            _FixedDetector([]),
            "does_not_exist",
            registry=registry,
            labels_dir=_LABELS_DIR,
            corpus_base_dir=_COMMITTED,
        )


def test_evaluate_corpus_integrity_failure_is_structured(tmp_path: Path) -> None:
    labels_dir = tmp_path / "labels"
    corpus_base = tmp_path / "corpus"
    labels_dir.mkdir()
    (corpus_base / "brokencorpus").mkdir(parents=True)  # empty -> labeled file missing

    labels = {
        "corpus_id": "broken",
        "language": "python",
        "version": "1",
        "labels": [
            {
                "label_id": "v1",
                "corpus_id": "broken",
                "language": "python",
                "location": {"file": "missing.py", "start_line": 1, "end_line": 1},
                "verdict": "vulnerable",
                "cwe": "CWE-89",
                "rule_id": None,
                "source": "test",
                "notes": None,
            }
        ],
    }
    (labels_dir / "broken.labels.json").write_text(json.dumps(labels), encoding="utf-8")

    registry_json = {
        "version": "1",
        "corpora": [
            {
                "id": "broken",
                "name": "Broken",
                "kind": "project_curated",
                "language": "python",
                "source_ref": None,
                "checksum": None,
                "local_path": "brokencorpus",
                "labels_path": "broken.labels.json",
                "license": "MIT",
                "notes": None,
            }
        ],
    }
    registry_path = tmp_path / "corpus_registry.json"
    registry_path.write_text(json.dumps(registry_json), encoding="utf-8")
    registry = load_corpus_registry(registry_path)

    result = evaluate_corpus(
        _RaisingDetector(),  # must not be invoked
        "broken",
        registry=registry,
        labels_dir=labels_dir,
        corpus_base_dir=corpus_base,
    )

    assert result.status is EvaluationStatus.INTEGRITY_FAILED
    assert result.metrics is None
    assert result.evaluation is None
    assert not result.integrity.ok


def test_evaluation_result_is_serializable() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    result = evaluate_corpus(
        _FixedDetector([_finding("dom_xss/vulnerable.js", 5)]),
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )

    dumped = result.model_dump(mode="json")
    assert dumped["status"] == "evaluated"
    assert dumped["corpus_id"] == "web_curated_js"
    assert dumped["metrics"]["precision"] == 1.0  # only the TP flagged -> precision 1.0
    json.dumps(dumped)  # end-to-end JSON serializable


def test_evaluation_result_is_frozen() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    result = evaluate_corpus(
        _FixedDetector([]),
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )
    with pytest.raises(ValidationError):
        result.corpus_id = "other"


def test_evaluation_result_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        EvaluationResult.model_validate(
            {
                "corpus_id": "c",
                "status": "evaluated",
                "detector_name": None,
                "integrity": {"corpus_id": "c", "issues": []},
                "evaluation": None,
                "metrics": None,
                "unexpected": "x",
            }
        )
