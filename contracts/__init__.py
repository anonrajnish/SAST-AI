"""Shared analysis contract.

The neutral home for the types produced by analyzers and consumed by the evaluation
harness and the scan pipeline: :class:`Language`, :class:`SourceLocation`,
:class:`Finding`, and the :class:`Detector` protocol (plus their validated field types).
Both the backend and the eval harness import from here so neither depends on the other.
"""

from __future__ import annotations

from ._contract import (
    CweStr,
    Detector,
    Finding,
    Language,
    NonEmptyStr,
    RelativePath,
    SourceLocation,
)

__all__ = [
    "CweStr",
    "Detector",
    "Finding",
    "Language",
    "NonEmptyStr",
    "RelativePath",
    "SourceLocation",
]
