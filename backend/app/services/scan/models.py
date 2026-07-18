"""Configuration models for the scan pipeline.

Defines how target languages are chosen (:class:`TargetMode`, :class:`ScanConfig`). The
coarse language grouping (:class:`~contracts.LanguageGroup`) is shared vocabulary and lives
in ``contracts`` so both this config and the deterministic analyzer registry can use it.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Self

from contracts import LanguageGroup
from pydantic import BaseModel, ConfigDict, model_validator


class TargetMode(StrEnum):
    """How target languages are chosen for a scan."""

    AUTO = "auto"
    MANUAL = "manual"


class ScanConfig(BaseModel):
    """Configuration for one scan: how to choose target languages, and which.

    ``AUTO`` lets the pipeline detect supported languages (``groups`` must be empty);
    ``MANUAL`` scans exactly the selected ``groups`` (at least one required), ignoring
    any other languages present in the repository.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: TargetMode
    groups: frozenset[LanguageGroup] = frozenset()

    @model_validator(mode="after")
    def _check_mode_groups(self) -> Self:
        if self.mode is TargetMode.AUTO and self.groups:
            raise ValueError("AUTO mode must not specify language groups")
        if self.mode is TargetMode.MANUAL and not self.groups:
            raise ValueError("MANUAL mode requires at least one language group")
        return self

    @classmethod
    def auto(cls) -> ScanConfig:
        """Build an AUTO-detect configuration."""

        return cls(mode=TargetMode.AUTO)

    @classmethod
    def manual(cls, groups: Iterable[LanguageGroup]) -> ScanConfig:
        """Build a MANUAL configuration for the given (non-empty) groups."""

        return cls(mode=TargetMode.MANUAL, groups=frozenset(groups))
