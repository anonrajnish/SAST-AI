"""Typed exceptions for the evaluation harness.

A single hierarchy rooted at :class:`EvalHarnessError` so callers (the runner in
TASK-020b and the metrics reporter in TASK-020c) can catch harness failures
distinctly from unexpected programming errors.
"""

from __future__ import annotations


class EvalHarnessError(Exception):
    """Base class for all evaluation-harness errors."""


class LabelFileError(EvalHarnessError):
    """A label file could not be read or did not contain valid JSON.

    Also raised when a resolved label path would escape its base directory.
    """


class LabelSchemaError(EvalHarnessError):
    """A label file parsed as JSON but failed schema validation."""


class CorpusRegistryError(EvalHarnessError):
    """The corpus registry could not be loaded, is invalid, or lacks a corpus."""
