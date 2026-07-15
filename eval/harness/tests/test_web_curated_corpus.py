"""Integrity tests for the committed curated Web (JS/TS/HTML) evaluation corpus.

The MVP "Web" analysis capability spans three single-language corpora — JavaScript,
TypeScript, and HTML. Each is loaded through the public loader (via its registry
descriptor) and checked against its committed corpus tree with the integrity
validator, so the corpus and its labels cannot drift out of sync.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ..loader import load_corpus_registry, load_labels_for_corpus
from ..models import Verdict
from ..validator import validate_label_set_against_corpus

_REPO_ROOT = Path(__file__).parents[3]
_EVAL = _REPO_ROOT / "eval"
_REGISTRY = _EVAL / "corpus_registry.json"
_LABELS_DIR = _EVAL / "labels"
_COMMITTED = _EVAL / "corpus" / "committed"

# corpus_id -> (expected language, expected CWE set)
_WEB_CORPORA: dict[str, tuple[str, set[str]]] = {
    "web_curated_js": ("javascript", {"CWE-79", "CWE-95"}),
    "web_curated_ts": ("typescript", {"CWE-79", "CWE-798"}),
    "web_curated_html": ("html", {"CWE-79", "CWE-1022"}),
}


@pytest.mark.parametrize("corpus_id", sorted(_WEB_CORPORA))
def test_web_curated_labels_load_and_validate(corpus_id: str) -> None:
    registry = load_corpus_registry(_REGISTRY)
    label_set = load_labels_for_corpus(registry, corpus_id, _LABELS_DIR)

    expected_language, _ = _WEB_CORPORA[corpus_id]
    assert label_set.language.value == expected_language
    assert len(label_set.labels) == 4
    assert label_set.n_vulnerable == 2
    assert label_set.n_safe == 2

    descriptor = next(corpus for corpus in registry.corpora if corpus.id == corpus_id)
    corpus_root = _COMMITTED / descriptor.local_path
    report = validate_label_set_against_corpus(label_set, corpus_root)
    assert report.ok, [issue.model_dump() for issue in report.issues]


@pytest.mark.parametrize("corpus_id", sorted(_WEB_CORPORA))
def test_web_curated_categories_balanced(corpus_id: str) -> None:
    registry = load_corpus_registry(_REGISTRY)
    label_set = load_labels_for_corpus(registry, corpus_id, _LABELS_DIR)

    _, expected_cwes = _WEB_CORPORA[corpus_id]
    assert {label.cwe for label in label_set.labels} == expected_cwes
    for cwe in expected_cwes:
        in_category = [label for label in label_set.labels if label.cwe == cwe]
        vulnerable = [lbl for lbl in in_category if lbl.verdict is Verdict.VULNERABLE]
        safe = [lbl for lbl in in_category if lbl.verdict is Verdict.SAFE]
        assert len(vulnerable) == 1, cwe
        assert len(safe) == 1, cwe
