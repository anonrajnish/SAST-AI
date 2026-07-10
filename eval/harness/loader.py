"""Read-only loaders for evaluation-harness ground truth.

Parses and validates label sets and the corpus registry from JSON. No network
access and no code execution occur here: the loader only reads files and
validates them against the models in :mod:`eval.harness.models`. All errors are
raised as typed :mod:`eval.harness.errors` exceptions.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .errors import CorpusRegistryError, EvalHarnessError, LabelFileError, LabelSchemaError
from .models import CorpusRegistry, LabelSet


def _read_json(path: Path, error_type: type[EvalHarnessError]) -> object:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise error_type(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise error_type(f"invalid JSON in {path}: {exc}") from exc


def resolve_within_directory(base: Path, relative: str) -> Path:
    """Resolve ``relative`` under ``base`` and reject any path that escapes it.

    Defense in depth against path traversal: even though descriptor paths are
    validated as relative at model construction, the resolved location is
    re-checked here before any file is opened (AI_DEVELOPMENT_GUIDE §8).
    """

    base_resolved = base.resolve()
    candidate = (base_resolved / relative).resolve()
    if candidate != base_resolved and base_resolved not in candidate.parents:
        raise LabelFileError(f"resolved path {candidate} escapes base directory {base_resolved}")
    return candidate


def load_label_set(path: Path) -> LabelSet:
    """Load and validate a single label set file."""

    raw = _read_json(path, LabelFileError)
    try:
        return LabelSet.model_validate(raw)
    except ValidationError as exc:
        raise LabelSchemaError(f"invalid label set in {path}: {exc}") from exc


def load_corpus_registry(path: Path) -> CorpusRegistry:
    """Load and validate the corpus registry file."""

    raw = _read_json(path, CorpusRegistryError)
    try:
        return CorpusRegistry.model_validate(raw)
    except ValidationError as exc:
        raise CorpusRegistryError(f"invalid corpus registry in {path}: {exc}") from exc


def load_labels_for_corpus(
    registry: CorpusRegistry, corpus_id: str, labels_dir: Path
) -> LabelSet:
    """Load the label set for ``corpus_id`` using its registry descriptor.

    Raises :class:`CorpusRegistryError` if the corpus is unknown, and reuses
    :func:`load_label_set` (so label file/schema errors surface as
    :class:`LabelFileError` / :class:`LabelSchemaError`).
    """

    descriptor = next((corpus for corpus in registry.corpora if corpus.id == corpus_id), None)
    if descriptor is None:
        raise CorpusRegistryError(f"unknown corpus_id: {corpus_id!r}")

    label_path = resolve_within_directory(labels_dir, descriptor.labels_path)
    label_set = load_label_set(label_path)
    if label_set.corpus_id != descriptor.id:
        raise LabelSchemaError(
            f"label set corpus_id {label_set.corpus_id!r} does not match "
            f"registry corpus id {descriptor.id!r}"
        )
    return label_set
