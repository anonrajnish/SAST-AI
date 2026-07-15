"""Integrity test for the committed ``project_curated`` evaluation corpus.

Ensures the shipped labels load through the public loader and pass the
integrity validator against the committed corpus tree, so the corpus and its
labels cannot drift out of sync.
"""

from __future__ import annotations

from pathlib import Path

from ..loader import load_label_set
from ..models import Verdict
from ..validator import validate_label_set_against_corpus

_REPO_ROOT = Path(__file__).parents[3]
_LABELS = _REPO_ROOT / "eval" / "labels" / "project-curated.labels.json"
_CORPUS_ROOT = _REPO_ROOT / "eval" / "corpus" / "committed" / "project-curated"

_EXPECTED_CWES = {"CWE-89", "CWE-79", "CWE-78", "CWE-22", "CWE-798"}


def test_project_curated_labels_load_and_validate() -> None:
    label_set = load_label_set(_LABELS)

    assert label_set.corpus_id == "project_curated"
    assert len(label_set.labels) == 20
    assert label_set.n_vulnerable == 10
    assert label_set.n_safe == 10

    report = validate_label_set_against_corpus(label_set, _CORPUS_ROOT)
    assert report.ok, [issue.model_dump() for issue in report.issues]


def test_project_curated_covers_five_categories_evenly() -> None:
    label_set = load_label_set(_LABELS)

    assert {label.cwe for label in label_set.labels} == _EXPECTED_CWES
    for cwe in _EXPECTED_CWES:
        in_category = [label for label in label_set.labels if label.cwe == cwe]
        vulnerable = [lbl for lbl in in_category if lbl.verdict is Verdict.VULNERABLE]
        safe = [lbl for lbl in in_category if lbl.verdict is Verdict.SAFE]
        assert len(vulnerable) == 2, cwe
        assert len(safe) == 2, cwe
