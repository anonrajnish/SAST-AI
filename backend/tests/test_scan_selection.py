"""Unit tests for registry-driven analyzer selection (Slice 2)."""

from __future__ import annotations

from app.services.deterministic import ANALYZER_REGISTRY, ANALYZERS_BY_NAME
from app.services.scan import LanguageGroup, select_analyzers

_PY = LanguageGroup.PYTHON
_WEB = LanguageGroup.WEB

# Registry order (single source of truth).
_ALL = [
    "secret-scanner",
    "code-execution-scanner",
    "weak-crypto-scanner",
    "unsafe-deserialization-scanner",
    "tls-verification-scanner",
    "reverse-tabnabbing-scanner",
]
# Reverse tabnabbing is Web-only, so it is excluded from a Python-only scan.
_PYTHON_APPLICABLE = _ALL[:-1]


def _names(analyzers: object) -> list[str]:
    assert isinstance(analyzers, tuple)
    return [a.detector_name for a in analyzers]


def test_select_python_group() -> None:
    assert _names(select_analyzers(frozenset({_PY}))) == _PYTHON_APPLICABLE


def test_select_web_group() -> None:
    assert _names(select_analyzers(frozenset({_WEB}))) == _ALL


def test_select_python_and_web() -> None:
    assert _names(select_analyzers(frozenset({_PY, _WEB}))) == _ALL


def test_select_empty_groups_selects_nothing() -> None:
    assert select_analyzers(frozenset()) == ()


def test_selection_preserves_registry_order_and_identity() -> None:
    selected = select_analyzers(frozenset({_PY, _WEB}))
    assert [a.detector_name for a in selected] == [
        e.analyzer.detector_name for e in ANALYZER_REGISTRY
    ]
    # returns the very analyzer instances from the registry (single source of truth)
    assert selected[0] is ANALYZERS_BY_NAME["secret-scanner"]


def test_registry_metadata_groups_are_well_formed() -> None:
    supported = {LanguageGroup.PYTHON, LanguageGroup.WEB}
    for entry in ANALYZER_REGISTRY:
        assert entry.language_groups  # every analyzer targets at least one group
        assert entry.language_groups <= supported
        assert entry.cwes  # every analyzer declares at least one CWE
    by_name = {e.analyzer.detector_name: e for e in ANALYZER_REGISTRY}
    assert by_name["reverse-tabnabbing-scanner"].language_groups == frozenset({_WEB})
    assert by_name["secret-scanner"].language_groups == {_PY, _WEB}
