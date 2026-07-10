"""Referential-integrity validation of ground-truth labels against a corpus tree.

Given a loaded :class:`~eval.harness.models.LabelSet` and a corpus root directory,
this module checks that every label points at a real location: the file exists as
a regular file within the corpus root, and any declared line range falls within
the file. Problems are returned as a structured :class:`IntegrityReport` — the
validator is read-only and **never imports or executes corpus code** (it only
stat-s files and counts their lines). This is the mechanism later TASK-020a
slices (curated authoring, OWASP/Juliet acquisition) rely on to trust labels;
rule execution and precision/recall live in TASK-020b / TASK-020c.
"""

from __future__ import annotations

import codecs
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .errors import LabelFileError
from .loader import resolve_within_directory
from .models import GroundTruthLabel, LabelSet

_READ_CHUNK_BYTES = 65536


class IntegrityIssueKind(StrEnum):
    """The category of a label-integrity problem."""

    INVALID_CORPUS_ROOT = "invalid_corpus_root"
    MISSING_FILE = "missing_file"
    NOT_A_FILE = "not_a_file"
    LINE_OUT_OF_RANGE = "line_out_of_range"
    UNDECODABLE_FILE = "undecodable_file"
    PATH_ESCAPE = "path_escape"


class IntegrityIssue(BaseModel):
    """A single integrity problem, with structured location context.

    ``label_id`` and ``file`` are optional so corpus-level problems (e.g. an
    invalid corpus root) can be represented without inventing a label.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: IntegrityIssueKind
    detail: str
    label_id: str | None = None
    file: str | None = None
    line: int | None = None


class IntegrityReport(BaseModel):
    """The outcome of validating a label set against a corpus tree."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_id: str
    issues: list[IntegrityIssue]

    @property
    def ok(self) -> bool:
        """True when no integrity issues were found."""

        return not self.issues

    @property
    def n_issues(self) -> int:
        """Number of integrity issues found."""

        return len(self.issues)


def _count_lines(path: Path) -> int | None:
    """Return the number of text lines in a UTF-8 file, or ``None`` if the file
    is not valid UTF-8.

    Streamed in fixed-size chunks so large corpus files are not loaded whole
    into memory (AI_DEVELOPMENT_GUIDE §13). A line is counted for trailing
    content that is not newline-terminated, matching editor line numbering.
    """

    decoder = codecs.getincrementaldecoder("utf-8")()
    newlines = 0
    any_content = False
    last_char = ""
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(_READ_CHUNK_BYTES), b""):
                text = decoder.decode(chunk)
                if text:
                    any_content = True
                    last_char = text[-1]
                    newlines += text.count("\n")
            tail = decoder.decode(b"", final=True)
            if tail:
                any_content = True
                last_char = tail[-1]
                newlines += tail.count("\n")
    except UnicodeDecodeError:
        return None
    if not any_content:
        return 0
    return newlines + (0 if last_char == "\n" else 1)


def _highest_labeled_line(label: GroundTruthLabel) -> int | None:
    lines = [
        value
        for value in (label.location.start_line, label.location.end_line)
        if value is not None
    ]
    return max(lines) if lines else None


def _check_label(label: GroundTruthLabel, corpus_root: Path) -> IntegrityIssue | None:
    relative = label.location.file
    try:
        resolved = resolve_within_directory(corpus_root, relative)
    except LabelFileError:
        return IntegrityIssue(
            kind=IntegrityIssueKind.PATH_ESCAPE,
            detail=f"{relative!r} resolves outside the corpus root",
            label_id=label.label_id,
            file=relative,
        )

    if not resolved.exists():
        return IntegrityIssue(
            kind=IntegrityIssueKind.MISSING_FILE,
            detail=f"labeled file {relative!r} does not exist under the corpus root",
            label_id=label.label_id,
            file=relative,
        )
    if not resolved.is_file():
        return IntegrityIssue(
            kind=IntegrityIssueKind.NOT_A_FILE,
            detail=f"labeled path {relative!r} is not a regular file",
            label_id=label.label_id,
            file=relative,
        )

    highest_line = _highest_labeled_line(label)
    if highest_line is None:
        return None

    line_count = _count_lines(resolved)
    if line_count is None:
        return IntegrityIssue(
            kind=IntegrityIssueKind.UNDECODABLE_FILE,
            detail=f"labeled file {relative!r} is not valid UTF-8; cannot verify line range",
            label_id=label.label_id,
            file=relative,
        )
    if highest_line > line_count:
        return IntegrityIssue(
            kind=IntegrityIssueKind.LINE_OUT_OF_RANGE,
            detail=f"line {highest_line} exceeds file length {line_count}",
            label_id=label.label_id,
            file=relative,
            line=highest_line,
        )
    return None


def validate_label_set_against_corpus(label_set: LabelSet, corpus_root: Path) -> IntegrityReport:
    """Validate that every label in ``label_set`` references a real location.

    Read-only: labeled files are stat-ed and their lines counted, never imported
    or executed. An unusable ``corpus_root`` is reported as an
    ``INVALID_CORPUS_ROOT`` issue rather than raised, so a caller can always
    inspect a single report.
    """

    if not corpus_root.is_dir():
        return IntegrityReport(
            corpus_id=label_set.corpus_id,
            issues=[
                IntegrityIssue(
                    kind=IntegrityIssueKind.INVALID_CORPUS_ROOT,
                    detail=f"corpus root {corpus_root} is not an existing directory",
                )
            ],
        )

    issues: list[IntegrityIssue] = []
    for label in label_set.labels:
        issue = _check_label(label, corpus_root)
        if issue is not None:
            issues.append(issue)
    return IntegrityReport(corpus_id=label_set.corpus_id, issues=issues)
