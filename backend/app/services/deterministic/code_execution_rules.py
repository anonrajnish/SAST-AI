"""Rule pack for dynamic code execution (CWE-95 / CWE-94).

High-confidence, single-line dangerous-API rules: a call to a language's
code-evaluation primitive (``eval``/``exec`` in Python; ``eval`` or the ``Function``
constructor in JavaScript/TypeScript). Method-qualified names (e.g.
``ast.literal_eval``) are excluded via a look-behind, so safe alternatives are not
flagged. No data-flow — the presence of the primitive is the finding.
"""

from __future__ import annotations

from eval.harness.models import Language

from .rules import PatternRule

_PYTHON = frozenset({Language.PYTHON})
_JS_TS = frozenset({Language.JAVASCRIPT, Language.TYPESCRIPT})

PYTHON_DYNAMIC_EXEC_RULE = PatternRule(
    id="python-dynamic-exec",
    name="Dynamic code execution via eval/exec",
    cwe="CWE-95",
    languages=_PYTHON,
    pattern=r"(?<![.\w])(?:eval|exec)\s*\(",
)

JS_DYNAMIC_EXEC_RULE = PatternRule(
    id="js-dynamic-exec",
    name="Dynamic code execution via eval or the Function constructor",
    cwe="CWE-95",
    languages=_JS_TS,
    pattern=r"(?<![.\w])eval\s*\(|(?<![.\w])new\s+Function\s*\(",
)

CODE_EXECUTION_RULES: tuple[PatternRule, ...] = (
    PYTHON_DYNAMIC_EXEC_RULE,
    JS_DYNAMIC_EXEC_RULE,
)
