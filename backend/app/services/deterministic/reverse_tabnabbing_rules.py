"""Rule pack for reverse tabnabbing (CWE-1022: Use of Web Link to Untrusted Target with
window.opener Access).

High-confidence, single-line rules for new-tab links that omit the noopener/noreferrer
mitigation. HTML: an ``<a>`` tag with ``target="_blank"`` but no ``rel="noopener"`` /
``rel="noreferrer"`` in the same tag — matched **case-insensitively**, so ``TARGET``/``Target``
and ``_BLANK`` are detected too. JavaScript/TypeScript: ``window.open(..., "_blank")`` without
``noopener`` in the call. The mitigated forms (``rel="noopener"``, ``rel="noreferrer"``,
``rel="noopener noreferrer"``, ``window.open(..., "noopener")``) are structurally excluded.

Scope is limited to ``<a>`` links and ``window.open`` — non-link elements (``<form>``, ``<area>``)
are out of scope. Single-line only: multi-line tags and opener-nulling on a later line are out of
scope by design (no data-flow, no contextual browser-behavior analysis).
"""

from __future__ import annotations

from contracts import Language

from .rules import PatternRule

_HTML = frozenset({Language.HTML})
_JS_TS = frozenset({Language.JAVASCRIPT, Language.TYPESCRIPT})

_HTML_REVERSE_TABNABBING = (
    r"(?i)<a\b(?![^>]*(?:noopener|noreferrer))"
    r"[^>]*target\s*=\s*['\"]_blank['\"]"
)

_JS_REVERSE_TABNABBING = r"window\.open\s*\((?![^;]*noopener)[^;]*['\"]_blank['\"]"

HTML_REVERSE_TABNABBING_RULE = PatternRule(
    id="html-reverse-tabnabbing",
    name="Reverse tabnabbing: target=_blank without rel=noopener",
    cwe="CWE-1022",
    languages=_HTML,
    pattern=_HTML_REVERSE_TABNABBING,
)

JS_REVERSE_TABNABBING_RULE = PatternRule(
    id="js-reverse-tabnabbing",
    name="Reverse tabnabbing: window.open with _blank and no noopener",
    cwe="CWE-1022",
    languages=_JS_TS,
    pattern=_JS_REVERSE_TABNABBING,
)

REVERSE_TABNABBING_RULES: tuple[PatternRule, ...] = (
    HTML_REVERSE_TABNABBING_RULE,
    JS_REVERSE_TABNABBING_RULE,
)
