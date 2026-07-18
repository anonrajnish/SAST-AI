"""Shared analysis contract: the language vocabulary and the finding/detector types.

Relocated here from ``eval.harness`` so the backend analyzers and the scan pipeline no
longer depend on the *evaluation* package for their core value types (review item M3).
Both the backend (``app.services.*``) and the eval harness import these from ``contracts``;
neither package owns the other, and a :class:`Finding` is one class across the boundary.

Validation-only and read-only: all string paths are validated as relative POSIX paths so
malformed or hostile input cannot reference locations outside a scanned tree
(AI_DEVELOPMENT_GUIDE §8).
"""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Annotated, Protocol, Self, runtime_checkable

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

_CWE_PATTERN = re.compile(r"CWE-\d+")


class Language(StrEnum):
    """Source language of a file or corpus.

    Covers the approved multi-language roadmap: the MVP languages (Python, JavaScript,
    TypeScript, HTML) plus future-roadmap languages (Java, C/C++, Go, C#). The evaluation
    harness is language-agnostic — a corpus declares its language and the harness
    privileges none of them.
    """

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    CSHARP = "csharp"


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


NonEmptyStr = Annotated[str, AfterValidator(_ensure_nonempty)]
RelativePath = Annotated[str, AfterValidator(_ensure_relative_path)]
CweStr = Annotated[str, AfterValidator(_ensure_cwe)]


class SourceLocation(BaseModel):
    """A location within a scanned file.

    ``start_line``/``end_line`` are optional because some corpora label at file/test-case
    granularity rather than a specific line range.
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


class Finding(BaseModel):
    """A single location a detector reports as (potentially) vulnerable.

    Reuses :class:`SourceLocation` so a finding's file and line range carry the same
    relative-path/anti-traversal validation as a ground-truth label. ``cwe``/``rule_id``/
    ``detector`` are optional provenance metadata (never the matched source text).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    location: SourceLocation
    cwe: CweStr | None = None
    rule_id: NonEmptyStr | None = None
    detector: NonEmptyStr | None = None


@runtime_checkable
class Detector(Protocol):
    """Interface an analyzer implements to be scored by the harness or run by the pipeline.

    A detector is treated as an opaque static analyzer: it is handed the resolved root of
    a tree and returns findings as data. Concrete analyzers live in
    ``app.services.deterministic`` (backend); consumers depend only on this protocol.
    """

    def scan(self, corpus_root: Path) -> list[Finding]:
        """Statically analyze the tree at ``corpus_root`` and report findings."""
        ...
