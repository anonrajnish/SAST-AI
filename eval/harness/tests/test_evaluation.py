"""Tests for single-corpus evaluation orchestration (TASK-020b, Slice 2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ..errors import CorpusRegistryError
from ..evaluation import CorpusEvaluation, run_evaluation
from ..loader import load_corpus_registry, resolve_within_directory
from contracts import Finding, SourceLocation
from ..validator import IntegrityIssueKind

_REPO_ROOT = Path(__file__).parents[3]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY_PATH = _EVAL / "corpus_registry.json"
_LABELS_DIR = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"


class _FixedDetector:
    """Fake detector returning a preset finding list (no real analysis)."""

    def __init__(self, findings: list[Finding]) -> None:
        self._findings = findings

    def scan(self, corpus_root: Path) -> list[Finding]:
        return list(self._findings)


class _RecordingDetector:
    """Fake detector that records the corpus root it was handed."""

    def __init__(self) -> None:
        self.seen: Path | None = None

    def scan(self, corpus_root: Path) -> list[Finding]:
        self.seen = corpus_root
        return []


class _RaisingDetector:
    """Fake detector that fails if invoked (used to prove it is skipped)."""

    def scan(self, corpus_root: Path) -> list[Finding]:
        raise AssertionError("detector must not run when integrity fails")


def _finding(file: str, line: int) -> Finding:
    return Finding(location=SourceLocation(file=file, start_line=line, end_line=line))


def test_run_evaluation_scores_real_corpus() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    detector = _FixedDetector(
        [
            _finding("dom_xss/vulnerable.js", 5),  # -> true positive
            _finding("dom_xss/secure.js", 5),  # -> false positive (safe flagged)
        ]
    )

    result = run_evaluation(
        detector,
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )

    assert result.corpus_id == "web_curated_js"
    assert result.integrity.ok
    assert result.evaluated is True
    assert result.evaluation is not None
    assert result.evaluation.n_true_positive == 1
    assert result.evaluation.n_false_positive == 1
    assert result.evaluation.n_false_negative == 1  # eval_injection vuln not flagged


def test_run_evaluation_empty_detector_flags_all_vulnerable_as_missed() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)

    result = run_evaluation(
        _FixedDetector([]),
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )

    assert result.evaluated is True
    assert result.evaluation is not None
    assert result.evaluation.n_true_positive == 0
    assert result.evaluation.n_false_positive == 0
    assert result.evaluation.n_false_negative == 2  # both vulnerable labels missed


def test_run_evaluation_passes_resolved_corpus_root_to_detector() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    detector = _RecordingDetector()

    run_evaluation(
        detector,
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )

    assert detector.seen == resolve_within_directory(_COMMITTED, "web-curated/javascript")


def test_run_evaluation_unknown_corpus_raises() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    with pytest.raises(CorpusRegistryError):
        run_evaluation(
            _FixedDetector([]),
            "does_not_exist",
            registry=registry,
            labels_dir=_LABELS_DIR,
            corpus_base_dir=_COMMITTED,
        )


def test_run_evaluation_integrity_failure_returns_structured_outcome(tmp_path: Path) -> None:
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

    result = run_evaluation(
        _RaisingDetector(),  # must not be invoked
        "broken",
        registry=registry,
        labels_dir=labels_dir,
        corpus_base_dir=corpus_base,
    )

    assert result.evaluated is False
    assert result.evaluation is None
    assert not result.integrity.ok
    assert any(
        issue.kind is IntegrityIssueKind.MISSING_FILE for issue in result.integrity.issues
    )


def test_corpus_evaluation_is_frozen() -> None:
    registry = load_corpus_registry(_REGISTRY_PATH)
    result = run_evaluation(
        _FixedDetector([]),
        "web_curated_js",
        registry=registry,
        labels_dir=_LABELS_DIR,
        corpus_base_dir=_COMMITTED,
    )
    with pytest.raises(ValidationError):
        result.corpus_id = "other"


def test_corpus_evaluation_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        CorpusEvaluation.model_validate(
            {
                "corpus_id": "c",
                "integrity": {"corpus_id": "c", "issues": []},
                "evaluation": None,
                "unexpected": "x",
            }
        )
