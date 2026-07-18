"""Unit tests for scan-pipeline target-group resolution (Slice 2)."""

from __future__ import annotations

from app.services.scan import LanguageGroup, ScanConfig, resolve_target_groups

_PY = LanguageGroup.PYTHON
_WEB = LanguageGroup.WEB


def test_auto_resolves_to_detected_groups() -> None:
    config = ScanConfig.auto()
    assert resolve_target_groups(config, frozenset({_PY})) == frozenset({_PY})
    assert resolve_target_groups(config, frozenset({_PY, _WEB})) == frozenset({_PY, _WEB})


def test_auto_with_nothing_detected_resolves_to_empty() -> None:
    assert resolve_target_groups(ScanConfig.auto(), frozenset()) == frozenset()


def test_manual_uses_selected_groups() -> None:
    config = ScanConfig.manual({_WEB})
    assert resolve_target_groups(config, frozenset({_PY, _WEB})) == frozenset({_WEB})


def test_manual_ignores_detected_groups() -> None:
    # MANUAL Python selected, but only Web detected -> still resolves to Python.
    config = ScanConfig.manual({_PY})
    assert resolve_target_groups(config, frozenset({_WEB})) == frozenset({_PY})


def test_manual_both_groups() -> None:
    config = ScanConfig.manual({_PY, _WEB})
    assert resolve_target_groups(config, frozenset()) == frozenset({_PY, _WEB})
