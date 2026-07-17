"""Rule pack for hardcoded-secret detection (CWE-798).

A single high-confidence, single-line rule: a secret-suggestive identifier assigned
directly to a string literal. This flags the literal-assignment case and excludes
environment reads (where the right-hand side is not a string literal), with no
data-flow. Applies across all MVP languages (Python + Web).
"""

from __future__ import annotations

from eval.harness.models import Language

from .rules import PatternRule

_SECRET_LANGUAGES = frozenset(
    {Language.PYTHON, Language.JAVASCRIPT, Language.TYPESCRIPT, Language.HTML}
)

# Any quote that opens a string literal: double, single, or backtick.
_QUOTE_CLASS = "[\"'`]"

# secret-suggestive identifier  =  <opening quote of a string literal>
_HARDCODED_SECRET_PATTERN = (
    r"(?i)[A-Za-z0-9_]*"
    r"(password|passwd|pwd|secret|token|api[_-]?key|apikey|access[_-]?key)"
    r"[A-Za-z0-9_]*\s*=\s*" + _QUOTE_CLASS
)

HARDCODED_SECRET_RULE = PatternRule(
    id="hardcoded-secret-literal",
    name="Hardcoded secret assigned as a string literal",
    cwe="CWE-798",
    languages=_SECRET_LANGUAGES,
    pattern=_HARDCODED_SECRET_PATTERN,
)

SECRET_RULES: tuple[PatternRule, ...] = (HARDCODED_SECRET_RULE,)
