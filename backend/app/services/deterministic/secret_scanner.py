"""Hardcoded-secret scanner — the first deterministic analyzer.

Wraps the reusable scanning foundation (:mod:`app.services.deterministic.rules`)
with the hardcoded-secret rule pack and exposes the evaluation harness's
``Detector`` interface (``scan(corpus_root) -> list[Finding]``), so the harness can
score it via ``evaluate_corpus``. Deterministic, read-only, no data-flow/taint/AI.
Findings carry only file, location, rule id, and CWE — never the matched secret.
"""

from __future__ import annotations

from pathlib import Path

from eval.harness.runner import Finding

from .rules import scan_tree
from .secret_rules import SECRET_RULES

_DETECTOR_NAME = "secret-scanner"


class SecretScanner:
    """Deterministic hardcoded-secret analyzer (satisfies the ``Detector`` protocol)."""

    def scan(self, corpus_root: Path) -> list[Finding]:
        """Return hardcoded-secret findings for the tree under ``corpus_root``."""

        return scan_tree(corpus_root, SECRET_RULES, detector_name=_DETECTOR_NAME)
