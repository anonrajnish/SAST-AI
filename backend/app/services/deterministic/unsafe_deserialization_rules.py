"""Rule pack for unsafe deserialization (CWE-502: Deserialization of Untrusted Data).

High-confidence, single-line dangerous-API rules for widely recognized unsafe
deserialization primitives whose safe counterpart is a syntactically distinct API,
so precision stays high without any data-flow. Python: ``pickle.load`` / ``pickle.loads``
and ``yaml.load`` / ``yaml.load_all`` — the safe ``yaml.safe_load`` and ``json.loads`` are
structurally excluded. JavaScript/TypeScript: ``node-serialize``'s ``unserialize`` /
``serialize.unserialize`` — the safe ``JSON.parse`` is excluded.

Extended sinks (``dill``, ``marshal``, ``jsonpickle``, ``js-yaml``) are intentionally
deferred to a future enhancement to keep this rule pack focused and high-confidence.
No data-flow — the presence of the primitive is the finding.
"""

from __future__ import annotations

from contracts import Language

from .rules import PatternRule

_PYTHON = frozenset({Language.PYTHON})
_JS_TS = frozenset({Language.JAVASCRIPT, Language.TYPESCRIPT})

_PYTHON_UNSAFE_DESERIALIZATION = (
    r"(?<![.\w])pickle\.loads?\s*\("
    r"|(?<![.\w])yaml\.load(?:_all)?\s*\("
)

_JS_UNSAFE_DESERIALIZATION = r"\bunserialize\s*\("

PYTHON_UNSAFE_DESERIALIZATION_RULE = PatternRule(
    id="python-unsafe-deserialization",
    name="Unsafe deserialization via pickle or yaml.load",
    cwe="CWE-502",
    languages=_PYTHON,
    pattern=_PYTHON_UNSAFE_DESERIALIZATION,
)

JS_UNSAFE_DESERIALIZATION_RULE = PatternRule(
    id="js-unsafe-deserialization",
    name="Unsafe deserialization via node-serialize unserialize",
    cwe="CWE-502",
    languages=_JS_TS,
    pattern=_JS_UNSAFE_DESERIALIZATION,
)

UNSAFE_DESERIALIZATION_RULES: tuple[PatternRule, ...] = (
    PYTHON_UNSAFE_DESERIALIZATION_RULE,
    JS_UNSAFE_DESERIALIZATION_RULE,
)
