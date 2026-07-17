"""Rule pack for disabled TLS certificate verification (CWE-295: Improper Certificate Validation).

High-confidence, single-line rules for code that *explicitly* disables TLS certificate
verification, where the safe counterpart is a syntactically distinct token — so precision
stays high without any data-flow. Python: ``verify=False`` (requests/httpx kwarg and the
``session.verify = False`` attribute form) and ``ssl._create_unverified_context(``. The
verify pattern matches assignment forms only (``verify=False`` / ``verify = False`` /
``session.verify = False``) and never the comparison ``verify == False``. JavaScript/
TypeScript: ``rejectUnauthorized: false``.

Deliberately excluded (would require contextual/data-flow analysis or belong to another
weakness): ``urllib3.disable_warnings()`` (suppressing a warning does not prove verification
was disabled), ``http://`` vs ``https://`` (CWE-319), self-signed handling, custom cert
stores, ``NODE_TLS_REJECT_UNAUTHORIZED`` (environment configuration, a future enhancement).
No data-flow — the presence of the disabling flag is the finding.
"""

from __future__ import annotations

from eval.harness.models import Language

from .rules import PatternRule

_PYTHON = frozenset({Language.PYTHON})
_JS_TS = frozenset({Language.JAVASCRIPT, Language.TYPESCRIPT})

_PYTHON_TLS_VERIFICATION = (
    r"\bverify\s*=\s*False\b"
    r"|(?<![.\w])ssl\._create_unverified_context\s*\("
)

_JS_TLS_VERIFICATION = r"\brejectUnauthorized\s*:\s*false\b"

PYTHON_TLS_VERIFICATION_RULE = PatternRule(
    id="python-tls-verification-disabled",
    name="TLS certificate verification disabled",
    cwe="CWE-295",
    languages=_PYTHON,
    pattern=_PYTHON_TLS_VERIFICATION,
)

JS_TLS_VERIFICATION_RULE = PatternRule(
    id="js-tls-verification-disabled",
    name="TLS certificate verification disabled via rejectUnauthorized: false",
    cwe="CWE-295",
    languages=_JS_TS,
    pattern=_JS_TLS_VERIFICATION,
)

TLS_VERIFICATION_RULES: tuple[PatternRule, ...] = (
    PYTHON_TLS_VERIFICATION_RULE,
    JS_TLS_VERIFICATION_RULE,
)
