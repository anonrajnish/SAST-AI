"""Evaluation harness package.

The measuring instrument for the SAST engine (PROJECT_PLAN §1, Gate G0.2). It loads
known-answer corpora and their labels (:mod:`~eval.harness.loader`), gates label/corpus
referential integrity (:mod:`~eval.harness.validator`), scores a detector's findings
against ground truth (:mod:`~eval.harness.runner`, :mod:`~eval.harness.evaluation`), and
reports precision/recall/F1 (:mod:`~eval.harness.metrics`). :func:`eval.harness.interface.
evaluate_corpus` is the single callable entry point (TASK-020a/b/c + TASK-021, complete).

The harness is analyzer-agnostic: it depends only on the ``Detector`` protocol
(``scan(corpus_root) -> list[Finding]``). The deterministic analyzers that implement it
live in the backend application (``app.services.deterministic``).
"""
