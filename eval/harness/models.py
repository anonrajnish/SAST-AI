"""Typed data models for the evaluation harness ground-truth contract.

These Pydantic v2 models define the *labeling schema* (known vulnerable/safe locations
per corpus) and the *corpus registry* (descriptors of the corpora the harness scores
against). They are the single source of truth for the JSON files under ``eval/labels/``
and ``eval/corpus_registry.json``.

The shared analysis vocabulary — :class:`~contracts.Language`,
:class:`~contracts.SourceLocation`, and the validated string types — lives in the neutral
``contracts`` package and is reused here (re-exported for backward compatibility); only
corpus/label-specific types are defined below. No corpus data is fetched or executed here.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from contracts import CweStr, Language, NonEmptyStr, RelativePath, SourceLocation

__all__ = [
    "ChecksumStr",
    "CorpusDescriptor",
    "CorpusKind",
    "CorpusRegistry",
    "CweStr",
    "GroundTruthLabel",
    "Language",
    "LabelSet",
    "NonEmptyStr",
    "RelativePath",
    "SourceLocation",
    "Verdict",
]

_CHECKSUM_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


class CorpusKind(StrEnum):
    """Origin/type of a known-answer corpus."""

    OWASP_BENCHMARK = "owasp_benchmark"
    NIST_JULIET = "nist_juliet"
    PROJECT_CURATED = "project_curated"


class Verdict(StrEnum):
    """Ground-truth verdict for a labeled location."""

    VULNERABLE = "vulnerable"
    SAFE = "safe"


def _ensure_checksum(value: str) -> str:
    if not _CHECKSUM_PATTERN.fullmatch(value):
        raise ValueError("checksum must be 'sha256:<64 lowercase hex characters>'")
    return value


ChecksumStr = Annotated[str, AfterValidator(_ensure_checksum)]


class GroundTruthLabel(BaseModel):
    """A single ground-truth judgement about a location in a corpus."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label_id: NonEmptyStr
    corpus_id: NonEmptyStr
    language: Language
    location: SourceLocation
    verdict: Verdict
    cwe: CweStr | None = None
    rule_id: NonEmptyStr | None = None
    source: NonEmptyStr
    notes: str | None = None


class LabelSet(BaseModel):
    """All ground-truth labels for one corpus in one language."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_id: NonEmptyStr
    language: Language
    version: NonEmptyStr
    labels: Annotated[list[GroundTruthLabel], Field(min_length=1)]

    @model_validator(mode="after")
    def _check_labels(self) -> Self:
        label_ids = [label.label_id for label in self.labels]
        if len(set(label_ids)) != len(label_ids):
            raise ValueError("label_id values must be unique within a label set")
        for label in self.labels:
            if label.corpus_id != self.corpus_id:
                raise ValueError("every label.corpus_id must match the label set corpus_id")
            if label.language != self.language:
                raise ValueError("every label.language must match the label set language")
        return self

    @property
    def n_vulnerable(self) -> int:
        """Number of labels whose verdict is ``vulnerable``."""

        return sum(1 for label in self.labels if label.verdict is Verdict.VULNERABLE)

    @property
    def n_safe(self) -> int:
        """Number of labels whose verdict is ``safe``."""

        return sum(1 for label in self.labels if label.verdict is Verdict.SAFE)


class CorpusDescriptor(BaseModel):
    """Registry entry describing one corpus. Data is not fetched by this slice."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: NonEmptyStr
    name: NonEmptyStr
    kind: CorpusKind
    language: Language
    license: NonEmptyStr
    homepage: str | None = None
    source_ref: str | None = None
    checksum: ChecksumStr | None = None
    local_path: RelativePath
    labels_path: RelativePath
    notes: str | None = None


class CorpusRegistry(BaseModel):
    """The set of corpora the harness knows about."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: NonEmptyStr
    corpora: Annotated[list[CorpusDescriptor], Field(min_length=1)]

    @model_validator(mode="after")
    def _check_unique_ids(self) -> Self:
        ids = [corpus.id for corpus in self.corpora]
        if len(set(ids)) != len(ids):
            raise ValueError("corpus id values must be unique in the registry")
        return self
