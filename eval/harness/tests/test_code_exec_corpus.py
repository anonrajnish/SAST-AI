"""Integrity test for the committed code-execution curated corpus (CWE-95)."""

from __future__ import annotations

from pathlib import Path

from ..loader import load_corpus_registry, load_labels_for_corpus
from ..validator import validate_label_set_against_corpus

_REPO_ROOT = Path(__file__).parents[3]
_EVAL = _REPO_ROOT / "eval"


def test_code_exec_corpus_loads_and_validates() -> None:
    registry = load_corpus_registry(_EVAL / "corpus_registry.json")
    label_set = load_labels_for_corpus(registry, "code_exec_py", _EVAL / "labels")

    assert label_set.language.value == "python"
    assert len(label_set.labels) == 4
    assert label_set.n_vulnerable == 2
    assert label_set.n_safe == 2
    assert {label.cwe for label in label_set.labels} == {"CWE-95"}

    descriptor = next(corpus for corpus in registry.corpora if corpus.id == "code_exec_py")
    corpus_root = _EVAL / "corpus" / "committed" / descriptor.local_path
    report = validate_label_set_against_corpus(label_set, corpus_root)
    assert report.ok, [issue.model_dump() for issue in report.issues]
