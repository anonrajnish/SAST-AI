"""Unit tests for the evaluation-harness label-integrity validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from ..loader import load_label_set
from ..models import LabelSet
from ..validator import (
    IntegrityIssueKind,
    validate_label_set_against_corpus,
)

_FIXTURES = Path(__file__).parent / "fixtures"
_CORPUS_ROOT = _FIXTURES / "corpus" / "project-curated"


def _label(
    file: str,
    *,
    start: int | None = None,
    end: int | None = None,
    label_id: str = "label-1",
) -> dict[str, object]:
    location: dict[str, object] = {"file": file}
    if start is not None:
        location["start_line"] = start
    if end is not None:
        location["end_line"] = end
    return {
        "label_id": label_id,
        "corpus_id": "project_curated",
        "language": "python",
        "location": location,
        "verdict": "vulnerable",
        "cwe": "CWE-89",
        "source": "test",
    }


def _label_set(*labels: dict[str, object]) -> LabelSet:
    return LabelSet.model_validate(
        {
            "corpus_id": "project_curated",
            "language": "python",
            "version": "1",
            "labels": list(labels),
        }
    )


def test_report_ok_for_valid_labels() -> None:
    label_set = load_label_set(_FIXTURES / "valid_labels.json")
    report = validate_label_set_against_corpus(label_set, _CORPUS_ROOT)
    assert report.ok
    assert report.n_issues == 0
    assert report.corpus_id == "project_curated"


def test_no_line_range_passes_on_existence() -> None:
    report = validate_label_set_against_corpus(
        _label_set(_label("sqli/basic_query.py")), _CORPUS_ROOT
    )
    assert report.ok


def test_invalid_corpus_root_reported_not_raised(tmp_path: Path) -> None:
    report = validate_label_set_against_corpus(
        _label_set(_label("sqli/basic_query.py", start=1)), tmp_path / "missing"
    )
    assert not report.ok
    assert [issue.kind for issue in report.issues] == [IntegrityIssueKind.INVALID_CORPUS_ROOT]
    assert report.issues[0].label_id is None
    assert report.issues[0].file is None


def test_missing_file_reported() -> None:
    report = validate_label_set_against_corpus(
        _label_set(_label("sqli/nope.py", start=1)), _CORPUS_ROOT
    )
    (issue,) = report.issues
    assert issue.kind is IntegrityIssueKind.MISSING_FILE
    assert issue.file == "sqli/nope.py"
    assert issue.label_id == "label-1"


def test_not_a_file_reported() -> None:
    report = validate_label_set_against_corpus(
        _label_set(_label("sqli", start=1)), _CORPUS_ROOT
    )
    (issue,) = report.issues
    assert issue.kind is IntegrityIssueKind.NOT_A_FILE


def test_line_out_of_range_reported() -> None:
    report = validate_label_set_against_corpus(
        _label_set(_label("sqli/basic_query.py", start=1000, end=1001)), _CORPUS_ROOT
    )
    (issue,) = report.issues
    assert issue.kind is IntegrityIssueKind.LINE_OUT_OF_RANGE
    assert issue.line == 1001
    assert issue.file == "sqli/basic_query.py"


def test_line_range_boundary_is_inclusive(tmp_path: Path) -> None:
    source = tmp_path / "f.py"
    source.write_text("x\n" * 10, encoding="utf-8")
    ok_report = validate_label_set_against_corpus(
        _label_set(_label("f.py", start=10, end=10)), tmp_path
    )
    assert ok_report.ok
    over_report = validate_label_set_against_corpus(
        _label_set(_label("f.py", start=10, end=11)), tmp_path
    )
    assert [issue.kind for issue in over_report.issues] == [
        IntegrityIssueKind.LINE_OUT_OF_RANGE
    ]


def test_undecodable_file_reported(tmp_path: Path) -> None:
    (tmp_path / "bin.py").write_bytes(b"\xff\xfe\x00\x01\n")
    report = validate_label_set_against_corpus(
        _label_set(_label("bin.py", start=1)), tmp_path
    )
    (issue,) = report.issues
    assert issue.kind is IntegrityIssueKind.UNDECODABLE_FILE


def test_path_escape_via_symlink_reported(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("a\nb\nc\n", encoding="utf-8")
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    link = corpus / "link.py"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported on this platform")
    report = validate_label_set_against_corpus(
        _label_set(_label("link.py", start=1)), corpus
    )
    (issue,) = report.issues
    assert issue.kind is IntegrityIssueKind.PATH_ESCAPE


def test_mixed_labels_report_only_failures() -> None:
    report = validate_label_set_against_corpus(
        _label_set(
            _label("sqli/basic_query.py", start=1, label_id="good"),
            _label("sqli/nope.py", start=1, label_id="bad"),
        ),
        _CORPUS_ROOT,
    )
    assert report.n_issues == 1
    assert report.issues[0].label_id == "bad"
