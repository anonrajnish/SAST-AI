"""Integrity tests for the committed deterministic-analyzer curated corpora.

One parametrized test covers every single-CWE analyzer micro-corpus (2 vulnerable +
2 safe). The broader ``project_curated`` and ``web_curated_*`` corpora keep their own
dedicated tests because they have a different shape (multiple categories/CWEs).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ..loader import load_corpus_registry, load_labels_for_corpus
from ..validator import validate_label_set_against_corpus

_REPO_ROOT = Path(__file__).parents[3]
_EVAL = _REPO_ROOT / "eval"

# (corpus_id, expected language, expected CWE set)
_ANALYZER_CORPORA: list[tuple[str, str, set[str]]] = [
    ("code_exec_py", "python", {"CWE-95"}),
    ("weak_crypto_py", "python", {"CWE-327", "CWE-328"}),
    ("weak_crypto_js", "javascript", {"CWE-327", "CWE-328"}),
    ("unsafe_deserialization_py", "python", {"CWE-502"}),
    ("unsafe_deserialization_js", "javascript", {"CWE-502"}),
    ("tls_verification_py", "python", {"CWE-295"}),
    ("tls_verification_js", "javascript", {"CWE-295"}),
    ("reverse_tabnabbing_html", "html", {"CWE-1022"}),
    ("reverse_tabnabbing_js", "javascript", {"CWE-1022"}),
]


@pytest.mark.parametrize(
    ("corpus_id", "language", "cwes"),
    _ANALYZER_CORPORA,
    ids=[row[0] for row in _ANALYZER_CORPORA],
)
def test_analyzer_corpus_loads_and_validates(
    corpus_id: str, language: str, cwes: set[str]
) -> None:
    registry = load_corpus_registry(_EVAL / "corpus_registry.json")
    label_set = load_labels_for_corpus(registry, corpus_id, _EVAL / "labels")

    assert label_set.language.value == language
    assert len(label_set.labels) == 4
    assert label_set.n_vulnerable == 2
    assert label_set.n_safe == 2
    assert {label.cwe for label in label_set.labels} == cwes

    descriptor = next(corpus for corpus in registry.corpora if corpus.id == corpus_id)
    corpus_root = _EVAL / "corpus" / "committed" / descriptor.local_path
    report = validate_label_set_against_corpus(label_set, corpus_root)
    assert report.ok, [issue.model_dump() for issue in report.issues]
