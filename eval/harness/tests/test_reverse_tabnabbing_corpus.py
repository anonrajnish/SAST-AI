"""Integrity tests for the committed reverse-tabnabbing curated corpora (CWE-1022)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ..loader import load_corpus_registry, load_labels_for_corpus
from ..validator import validate_label_set_against_corpus

_REPO_ROOT = Path(__file__).parents[3]
_EVAL = _REPO_ROOT / "eval"

_CORPORA = {
    "reverse_tabnabbing_html": "html",
    "reverse_tabnabbing_js": "javascript",
}


@pytest.mark.parametrize("corpus_id", sorted(_CORPORA))
def test_reverse_tabnabbing_corpus_loads_and_validates(corpus_id: str) -> None:
    registry = load_corpus_registry(_EVAL / "corpus_registry.json")
    label_set = load_labels_for_corpus(registry, corpus_id, _EVAL / "labels")

    assert label_set.language.value == _CORPORA[corpus_id]
    assert len(label_set.labels) == 4
    assert label_set.n_vulnerable == 2
    assert label_set.n_safe == 2
    assert {label.cwe for label in label_set.labels} == {"CWE-1022"}

    descriptor = next(corpus for corpus in registry.corpora if corpus.id == corpus_id)
    corpus_root = _EVAL / "corpus" / "committed" / descriptor.local_path
    report = validate_label_set_against_corpus(label_set, corpus_root)
    assert report.ok, [issue.model_dump() for issue in report.issues]
