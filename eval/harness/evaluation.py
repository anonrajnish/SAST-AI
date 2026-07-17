"""Single-corpus evaluation orchestration for the eval runner (TASK-020b, Slice 2).

Wires the already-built harness components together: it loads a corpus's labels
(loader), gates them for referential integrity against the corpus tree
(validator), invokes a caller-supplied :class:`Detector` over the corpus root,
and scores its findings against the ground truth (matcher). It is
**analyzer-agnostic** — it knows only the :class:`Detector` protocol and the
:class:`~eval.harness.runner.Finding` type — and implements **no analyzer, no AI,
no metrics** (precision/recall/F1 is TASK-020c) and **no CLI/API** (TASK-021).

Integrity failure is an **expected evaluation outcome**, not an exception: when the
labels do not match the corpus tree, :func:`run_evaluation` returns a
:class:`CorpusEvaluation` whose ``evaluation`` is ``None`` and whose ``integrity``
report explains why, and the detector is not run. Exceptions are reserved for
genuine faults (unknown corpus id, unreadable/invalid label files, path escape),
which propagate as :mod:`eval.harness.errors` types from the loader.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from .loader import load_labels_for_corpus, resolve_within_directory
from .models import CorpusRegistry
from .runner import EvaluationReport, Finding, match_findings_to_labels
from .validator import IntegrityReport, validate_label_set_against_corpus


class Detector(Protocol):
    """Interface an analyzer implements to be scored by the harness.

    The harness treats a detector as an opaque static analyzer: it hands over the
    resolved corpus root and consumes the returned findings as data. No real
    analyzer is implemented in this slice.
    """

    def scan(self, corpus_root: Path) -> list[Finding]:
        """Statically analyze the corpus at ``corpus_root`` and report findings."""
        ...


class CorpusEvaluation(BaseModel):
    """Outcome of evaluating one corpus.

    ``integrity`` is always present. When integrity validation fails, ``evaluation``
    is ``None`` (the detector was not run and no scoring took place) and
    ``integrity`` explains why; otherwise ``evaluation`` holds the TP/FP/FN scoring.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    corpus_id: str
    integrity: IntegrityReport
    evaluation: EvaluationReport | None = None

    @property
    def evaluated(self) -> bool:
        """True when integrity passed and the detector's findings were scored."""

        return self.evaluation is not None


def run_evaluation(
    detector: Detector,
    corpus_id: str,
    *,
    registry: CorpusRegistry,
    labels_dir: Path,
    corpus_base_dir: Path,
) -> CorpusEvaluation:
    """Evaluate ``detector`` against one corpus and return a structured outcome.

    Loads the corpus's labels and resolves its committed tree (loader), gates the
    labels with the integrity validator, and — only if integrity passes — invokes
    ``detector.scan`` over the corpus root and scores the findings (matcher). If
    integrity fails the detector is not run and the returned
    :class:`CorpusEvaluation` has ``evaluation is None``.

    Raises :class:`~eval.harness.errors.CorpusRegistryError` for an unknown
    ``corpus_id`` and :class:`~eval.harness.errors.LabelFileError` /
    :class:`~eval.harness.errors.LabelSchemaError` for an unreadable or invalid
    label file (all from the loader).
    """

    label_set = load_labels_for_corpus(registry, corpus_id, labels_dir)
    descriptor = next(corpus for corpus in registry.corpora if corpus.id == corpus_id)
    corpus_root = resolve_within_directory(corpus_base_dir, descriptor.local_path)

    integrity = validate_label_set_against_corpus(label_set, corpus_root)
    if not integrity.ok:
        return CorpusEvaluation(corpus_id=corpus_id, integrity=integrity, evaluation=None)

    findings = detector.scan(corpus_root)
    evaluation = match_findings_to_labels(label_set, findings)
    return CorpusEvaluation(corpus_id=corpus_id, integrity=integrity, evaluation=evaluation)
