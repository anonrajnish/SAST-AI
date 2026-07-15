"""Typed data models for the evaluation harness ground-truth contract.

These Pydantic v2 models define the *labeling schema* (known vulnerable/safe
locations per corpus) and the *corpus registry* (descriptors of the corpora the
harness will later score against). They are the single source of truth for the
JSON files under ``eval/labels/`` and ``eval/corpus_registry.json``; downstream
tasks (the runner, TASK-020b, and the metrics reporter, TASK-020c) consume them.

No corpus data is fetched or executed here — this module only describes and
validates the ground truth. All string paths are validated as relative POSIX
paths so that malformed or hostile input cannot reference locations outside a
corpus (AI_DEVELOPMENT_GUIDE §8).
"""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

_CWE_PATTERN = re.compile(r"CWE-\d+")
_CHECKSUM_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


class Language(StrEnum):
    """Source language of a corpus.

    Covers the approved multi-language roadmap: the MVP languages (Python,
    JavaScript, TypeScript, HTML) plus future-roadmap languages (Java, C/C++,
    Go, C#). The evaluation harness itself is language-agnostic — a corpus
    declares its language here and the harness privileges none of them.
    """

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    CSHARP = "csharp"


class CorpusKind(StrEnum):
    """Origin/type of a known-answer corpus."""

    OWASP_BENCHMARK = "owasp_benchmark"
    NIST_JULIET = "nist_juliet"
    PROJECT_CURATED = "project_curated"


class Verdict(StrEnum):
    """Ground-truth verdict for a labeled location."""

    VULNERABLE = "vulnerable"
    SAFE = "safe"


def _ensure_nonempty(value: str) -> str:
    if not value.strip():
        raise ValueError("value must be a non-empty string")
    return value


def _ensure_relative_path(value: str) -> str:
    if not value.strip():
        raise ValueError("path must be a non-empty string")
    if "\x00" in value:
        raise ValueError("path must not contain a null byte")
    if "\\" in value:
        raise ValueError("path must use POSIX separators ('/')")
    pure = PurePosixPath(value)
    if pure.is_absolute():
        raise ValueError("path must be relative, not absolute")
    if ".." in pure.parts:
        raise ValueError("path must not contain '..' segments")
    return value


def _ensure_cwe(value: str) -> str:
    if not _CWE_PATTERN.fullmatch(value):
        raise ValueError("cwe must match 'CWE-<number>' (e.g. 'CWE-89')")
    return value


def _ensure_checksum(value: str) -> str:
    if not _CHECKSUM_PATTERN.fullmatch(value):
        raise ValueError("checksum must be 'sha256:<64 lowercase hex characters>'")
    return value


NonEmptyStr = Annotated[str, AfterValidator(_ensure_nonempty)]
RelativePath = Annotated[str, AfterValidator(_ensure_relative_path)]
CweStr = Annotated[str, AfterValidator(_ensure_cwe)]
ChecksumStr = Annotated[str, AfterValidator(_ensure_checksum)]


class SourceLocation(BaseModel):
    """A location within a corpus file.

    ``start_line``/``end_line`` are optional because some corpora label at
    file/test-case granularity rather than a specific line range.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    file: RelativePath
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _check_line_range(self) -> Self:
        if self.end_line is not None:
            if self.start_line is None:
                raise ValueError("end_line requires start_line")
            if self.end_line < self.start_line:
                raise ValueError("end_line must be >= start_line")
        return self


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
