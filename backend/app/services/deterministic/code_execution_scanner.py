"""Dynamic code execution analyzer (CWE-95 / CWE-94).

Second deterministic analyzer. Reuses :class:`PatternAnalyzer` unchanged and differs
from the secret scanner only by its rule pack. Deterministic, read-only, no
data-flow/taint/AI. Findings carry only file, location, rule id, and CWE.
"""

from __future__ import annotations

from .analyzer import PatternAnalyzer
from .code_execution_rules import CODE_EXECUTION_RULES


class CodeExecutionScanner(PatternAnalyzer):
    """Deterministic dynamic-code-execution analyzer (satisfies ``Detector``)."""

    def __init__(self) -> None:
        super().__init__(CODE_EXECUTION_RULES, "code-execution-scanner")
