"""Unit tests for the evaluation-harness loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from ..errors import CorpusRegistryError, LabelFileError, LabelSchemaError
from ..loader import (
    load_corpus_registry,
    load_label_set,
    load_labels_for_corpus,
    resolve_within_directory,
)
from ..models import CorpusRegistry

_FIXTURES = Path(__file__).parent / "fixtures"
_REPO_ROOT = Path(__file__).parents[3]


def _registry() -> CorpusRegistry:
    return CorpusRegistry.model_validate(
        {
            "version": "1",
            "corpora": [
                {
                    "id": "project_curated",
                    "name": "Project Curated",
                    "kind": "project_curated",
                    "language": "python",
                    "license": "MIT",
                    "local_path": "project-curated",
                    "labels_path": "valid_labels.json",
                }
            ],
        }
    )


def test_load_label_set_valid() -> None:
    label_set = load_label_set(_FIXTURES / "valid_labels.json")
    assert label_set.corpus_id == "project_curated"
    assert label_set.n_vulnerable == 1
    assert label_set.n_safe == 1


def test_load_label_set_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LabelFileError):
        load_label_set(tmp_path / "nope.json")


def test_load_label_set_malformed_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(LabelFileError):
        load_label_set(bad)


def test_load_label_set_schema_violation() -> None:
    with pytest.raises(LabelSchemaError):
        load_label_set(_FIXTURES / "invalid_labels.json")


def test_shipped_corpus_registry_is_valid() -> None:
    registry = load_corpus_registry(_REPO_ROOT / "eval" / "corpus_registry.json")
    assert {corpus.id for corpus in registry.corpora} == {
        "owasp_benchmark",
        "nist_juliet",
        "project_curated",
        "web_curated_js",
        "web_curated_ts",
        "web_curated_html",
    }


def test_load_corpus_registry_malformed_json(tmp_path: Path) -> None:
    bad = tmp_path / "registry.json"
    bad.write_text("[", encoding="utf-8")
    with pytest.raises(CorpusRegistryError):
        load_corpus_registry(bad)


def test_load_corpus_registry_duplicate_id(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    registry.write_text(
        (
            '{"version":"1","corpora":['
            '{"id":"dup","name":"A","kind":"project_curated","language":"python",'
            '"license":"MIT","local_path":"a","labels_path":"a.json"},'
            '{"id":"dup","name":"B","kind":"project_curated","language":"python",'
            '"license":"MIT","local_path":"b","labels_path":"b.json"}]}'
        ),
        encoding="utf-8",
    )
    with pytest.raises(CorpusRegistryError):
        load_corpus_registry(registry)


def test_load_labels_for_corpus_resolves_descriptor() -> None:
    label_set = load_labels_for_corpus(_registry(), "project_curated", _FIXTURES)
    assert label_set.corpus_id == "project_curated"


def test_load_labels_for_corpus_unknown_id() -> None:
    with pytest.raises(CorpusRegistryError):
        load_labels_for_corpus(_registry(), "does_not_exist", _FIXTURES)


def test_resolve_within_directory_accepts_relative(tmp_path: Path) -> None:
    resolved = resolve_within_directory(tmp_path, "sub/labels.json")
    assert resolved == (tmp_path / "sub" / "labels.json").resolve()


def test_resolve_within_directory_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(LabelFileError):
        resolve_within_directory(tmp_path, "../escape.json")
