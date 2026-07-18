"""Unit tests for the scan-pipeline configuration model (Slice 1)."""

from __future__ import annotations

import pytest
from app.services.scan import LanguageGroup, ScanConfig, TargetMode
from pydantic import ValidationError


def test_auto_config_has_no_groups() -> None:
    config = ScanConfig.auto()
    assert config.mode is TargetMode.AUTO
    assert config.groups == frozenset()


def test_auto_rejects_explicit_groups() -> None:
    with pytest.raises(ValidationError):
        ScanConfig(mode=TargetMode.AUTO, groups=frozenset({LanguageGroup.PYTHON}))


def test_manual_requires_at_least_one_group() -> None:
    with pytest.raises(ValidationError):
        ScanConfig(mode=TargetMode.MANUAL, groups=frozenset())


def test_manual_config_with_groups() -> None:
    config = ScanConfig.manual({LanguageGroup.PYTHON, LanguageGroup.WEB})
    assert config.mode is TargetMode.MANUAL
    assert config.groups == {LanguageGroup.PYTHON, LanguageGroup.WEB}


def test_manual_single_group() -> None:
    config = ScanConfig.manual({LanguageGroup.WEB})
    assert config.groups == frozenset({LanguageGroup.WEB})


def test_config_is_frozen() -> None:
    config = ScanConfig.auto()
    with pytest.raises(ValidationError):
        config.mode = TargetMode.MANUAL


def test_config_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        ScanConfig.model_validate({"mode": "auto", "groups": [], "unexpected": True})
