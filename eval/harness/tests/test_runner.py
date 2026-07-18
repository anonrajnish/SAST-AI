"""Unit tests for the eval runner's result contract and matching (TASK-020b)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from contracts import Finding, Language, SourceLocation

from ..models import GroundTruthLabel, LabelSet, Verdict
from ..runner import MatchOutcome, match_findings_to_labels


def _label(
    label_id: str,
    file: str,
    verdict: str,
    *,
    start: int | None = None,
    end: int | None = None,
    cwe: str | None = None,
) -> GroundTruthLabel:
    return GroundTruthLabel(
        label_id=label_id,
        corpus_id="c",
        language=Language.PYTHON,
        location=SourceLocation(file=file, start_line=start, end_line=end),
        verdict=Verdict(verdict),
        cwe=cwe,
        source="test",
    )


def _label_set(*labels: GroundTruthLabel) -> LabelSet:
    return LabelSet(corpus_id="c", language=Language.PYTHON, version="1", labels=list(labels))


def _finding(file: str, *, start: int | None = None, end: int | None = None) -> Finding:
    return Finding(location=SourceLocation(file=file, start_line=start, end_line=end))


def test_true_positive() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=5, end=5))
    report = match_findings_to_labels(label_set, [_finding("a.py", start=5, end=5)])

    assert report.n_true_positive == 1
    assert report.n_false_negative == 0
    assert report.n_false_positive == 0
    assert report.label_outcomes[0].outcome is MatchOutcome.TRUE_POSITIVE
    assert report.label_outcomes[0].matched_finding_count == 1
    assert report.unmatched_findings == []


def test_false_negative_when_vulnerable_label_unmatched() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=5, end=5))
    report = match_findings_to_labels(label_set, [])

    assert report.n_false_negative == 1
    assert report.label_outcomes[0].outcome is MatchOutcome.FALSE_NEGATIVE
    assert report.label_outcomes[0].matched_finding_count == 0


def test_false_positive_when_safe_label_matched() -> None:
    label_set = _label_set(_label("s1", "a.py", "safe", start=5, end=5))
    report = match_findings_to_labels(label_set, [_finding("a.py", start=5, end=5)])

    assert report.n_false_positive == 1
    assert report.label_outcomes[0].outcome is MatchOutcome.FALSE_POSITIVE
    assert report.label_outcomes[0].expected is Verdict.SAFE


def test_safe_label_unmatched_yields_no_outcome() -> None:
    # True negatives are intentionally out of scope: no outcome is recorded.
    label_set = _label_set(_label("s1", "a.py", "safe", start=5, end=5))
    report = match_findings_to_labels(label_set, [])

    assert report.label_outcomes == []
    assert report.n_true_positive == 0
    assert report.n_false_positive == 0
    assert report.n_false_negative == 0


def test_finding_outside_range_is_a_miss() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=5, end=5))
    report = match_findings_to_labels(label_set, [_finding("a.py", start=9, end=9)])

    assert report.n_false_negative == 1
    assert len(report.unmatched_findings) == 1


def test_different_file_is_a_miss() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=5, end=5))
    report = match_findings_to_labels(label_set, [_finding("b.py", start=5, end=5)])

    assert report.n_false_negative == 1
    assert len(report.unmatched_findings) == 1


def test_overlapping_range_matches() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=5, end=8))
    report = match_findings_to_labels(label_set, [_finding("a.py", start=6, end=6)])

    assert report.n_true_positive == 1


def test_whole_file_label_matches_any_finding_in_file() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable"))
    report = match_findings_to_labels(label_set, [_finding("a.py", start=42, end=42)])

    assert report.n_true_positive == 1


def test_multiple_findings_on_one_label_count() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=5, end=5))
    report = match_findings_to_labels(
        label_set, [_finding("a.py", start=5, end=5), _finding("a.py", start=5, end=5)]
    )

    assert report.n_true_positive == 1
    assert report.label_outcomes[0].matched_finding_count == 2
    assert report.unmatched_findings == []


def test_unmatched_findings_collected() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=5, end=5))
    report = match_findings_to_labels(
        label_set, [_finding("a.py", start=5, end=5), _finding("z.py", start=1, end=1)]
    )

    assert report.n_true_positive == 1
    assert len(report.unmatched_findings) == 1
    assert report.unmatched_findings[0].location.file == "z.py"


def test_report_corpus_id_propagates() -> None:
    label_set = _label_set(_label("v1", "a.py", "vulnerable", start=1, end=1))
    report = match_findings_to_labels(label_set, [])

    assert report.corpus_id == "c"


def test_enum_has_no_true_negative_member() -> None:
    assert {member.value for member in MatchOutcome} == {
        "true_positive",
        "false_positive",
        "false_negative",
    }


def test_finding_is_frozen() -> None:
    finding = _finding("a.py", start=1, end=1)
    with pytest.raises(ValidationError):
        finding.cwe = "CWE-79"


def test_finding_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        Finding.model_validate(
            {"location": {"file": "a.py", "start_line": 1}, "unexpected": "x"}
        )


def test_report_is_frozen() -> None:
    report = match_findings_to_labels(
        _label_set(_label("v1", "a.py", "vulnerable", start=1, end=1)), []
    )
    with pytest.raises(ValidationError):
        report.corpus_id = "other"
