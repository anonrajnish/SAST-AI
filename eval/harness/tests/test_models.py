"""Unit tests for the evaluation-harness ground-truth models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ..models import (
    CorpusDescriptor,
    CorpusKind,
    CorpusRegistry,
    GroundTruthLabel,
    Language,
    LabelSet,
    SourceLocation,
    Verdict,
)


def _label(**overrides: object) -> GroundTruthLabel:
    data: dict[str, object] = {
        "label_id": "curated-sqli-001",
        "corpus_id": "project_curated",
        "language": "python",
        "location": {"file": "sqli/basic_query.py", "start_line": 12, "end_line": 12},
        "verdict": "vulnerable",
        "cwe": "CWE-89",
        "source": "manual-curation",
    }
    data.update(overrides)
    return GroundTruthLabel.model_validate(data)


def _descriptor(**overrides: object) -> CorpusDescriptor:
    data: dict[str, object] = {
        "id": "project_curated",
        "name": "Project Curated",
        "kind": "project_curated",
        "language": "python",
        "license": "MIT",
        "local_path": "project-curated",
        "labels_path": "project-curated.labels.json",
    }
    data.update(overrides)
    return CorpusDescriptor.model_validate(data)


def test_valid_label_construction() -> None:
    label = _label()
    assert label.verdict is Verdict.VULNERABLE
    assert label.language is Language.PYTHON
    assert label.cwe == "CWE-89"


def test_label_rejects_bad_cwe() -> None:
    with pytest.raises(ValidationError):
        _label(cwe="89")


def test_label_allows_missing_cwe() -> None:
    assert _label(cwe=None, verdict="safe").cwe is None


def test_label_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        _label(unexpected="x")


def test_label_is_frozen() -> None:
    label = _label()
    with pytest.raises(ValidationError):
        label.verdict = Verdict.SAFE


def test_label_rejects_blank_identifier() -> None:
    with pytest.raises(ValidationError):
        _label(label_id="   ")


def test_source_location_rejects_zero_start_line() -> None:
    with pytest.raises(ValidationError):
        SourceLocation.model_validate({"file": "a.py", "start_line": 0})


def test_source_location_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError):
        SourceLocation.model_validate({"file": "a.py", "start_line": 5, "end_line": 3})


def test_source_location_rejects_end_without_start() -> None:
    with pytest.raises(ValidationError):
        SourceLocation.model_validate({"file": "a.py", "end_line": 5})


def test_source_location_rejects_absolute_path() -> None:
    with pytest.raises(ValidationError):
        SourceLocation.model_validate({"file": "/etc/passwd"})


def test_source_location_rejects_parent_traversal() -> None:
    with pytest.raises(ValidationError):
        SourceLocation.model_validate({"file": "../secrets.py"})


def test_source_location_rejects_backslash_path() -> None:
    with pytest.raises(ValidationError):
        SourceLocation.model_validate({"file": "sqli\\basic_query.py"})


def test_labelset_counts() -> None:
    label_set = LabelSet.model_validate(
        {
            "corpus_id": "project_curated",
            "language": "python",
            "version": "1",
            "labels": [
                _label().model_dump(),
                _label(label_id="curated-safe-001", verdict="safe", cwe=None).model_dump(),
            ],
        }
    )
    assert label_set.n_vulnerable == 1
    assert label_set.n_safe == 1


def test_labelset_rejects_duplicate_label_id() -> None:
    with pytest.raises(ValidationError):
        LabelSet.model_validate(
            {
                "corpus_id": "project_curated",
                "language": "python",
                "version": "1",
                "labels": [_label().model_dump(), _label().model_dump()],
            }
        )


def test_labelset_rejects_corpus_id_mismatch() -> None:
    with pytest.raises(ValidationError):
        LabelSet.model_validate(
            {
                "corpus_id": "project_curated",
                "language": "python",
                "version": "1",
                "labels": [_label(corpus_id="other").model_dump()],
            }
        )


def test_labelset_rejects_empty_labels() -> None:
    with pytest.raises(ValidationError):
        LabelSet.model_validate(
            {
                "corpus_id": "project_curated",
                "language": "python",
                "version": "1",
                "labels": [],
            }
        )


def test_descriptor_accepts_valid_checksum() -> None:
    descriptor = _descriptor(checksum="sha256:" + "a" * 64)
    assert descriptor.checksum == "sha256:" + "a" * 64


def test_descriptor_checksum_optional() -> None:
    assert _descriptor().checksum is None


def test_descriptor_rejects_bad_checksum() -> None:
    with pytest.raises(ValidationError):
        _descriptor(checksum="sha256:not-hex")


def test_descriptor_rejects_uppercase_checksum() -> None:
    with pytest.raises(ValidationError):
        _descriptor(checksum="sha256:" + "A" * 64)


def test_corpuskind_project_curated_value() -> None:
    assert CorpusKind.PROJECT_CURATED.value == "project_curated"


def test_descriptor_rejects_retired_kind_value() -> None:
    with pytest.raises(ValidationError):
        _descriptor(kind="curated_internal")


def test_registry_rejects_duplicate_id() -> None:
    with pytest.raises(ValidationError):
        CorpusRegistry.model_validate(
            {
                "version": "1",
                "corpora": [_descriptor().model_dump(), _descriptor().model_dump()],
            }
        )
