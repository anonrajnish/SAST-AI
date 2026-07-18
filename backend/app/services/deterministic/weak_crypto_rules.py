"""Rule pack for weak cryptography (CWE-327 broken cipher / CWE-328 weak hash).

High-confidence, single-line dangerous-API rules for universally recognized weak
algorithms — **MD5, SHA-1** (weak hashes) and **DES, 3DES, RC4** (weak ciphers).
The algorithm token is always anchored to a real crypto call/constructor (never a
bare ``md5``/``sha1`` substring in a name or comment), so precision stays high.
Strong algorithms (SHA-256/512, AES) are structurally excluded. No data-flow.

Blowfish is intentionally **not** flagged here: it is treated as a future Security
Best-Practice recommendation (migrate to AES), not a CWE-327/328 vulnerability.
"""

from __future__ import annotations

from contracts import Language

from .rules import PatternRule

_PYTHON = frozenset({Language.PYTHON})
_JS_TS = frozenset({Language.JAVASCRIPT, Language.TYPESCRIPT})

_PY_WEAK_HASH = (
    r"(?<![.\w])hashlib\.(?:md5|sha1)\s*\("
    r"|hashlib\.new\s*\(\s*['\"](?:md5|sha1)['\"]"
    r"|(?<![.\w])hashes\.(?:MD5|SHA1)\s*\("
)

_PY_WEAK_CIPHER = (
    r"(?<![.\w])(?:DES3|DES|ARC4)\.new\s*\("
    r"|algorithms\.(?:TripleDES|ARC4)\s*\("
)

_JS_WEAK_HASH = (
    r"createHash\s*\(\s*['\"](?:md5|sha1)['\"]"
    r"|CryptoJS\.(?:MD5|SHA1)\s*\("
)

_JS_WEAK_CIPHER = (
    r"createCipheriv\s*\(\s*['\"](?:des|rc4)"
    r"|CryptoJS\.(?:DES|TripleDES|RC4)\s*\("
)

PYTHON_WEAK_HASH_RULE = PatternRule(
    id="python-weak-hash",
    name="Weak hash algorithm (MD5/SHA-1)",
    cwe="CWE-328",
    languages=_PYTHON,
    pattern=_PY_WEAK_HASH,
)

PYTHON_WEAK_CIPHER_RULE = PatternRule(
    id="python-weak-cipher",
    name="Weak cipher algorithm (DES/3DES/RC4)",
    cwe="CWE-327",
    languages=_PYTHON,
    pattern=_PY_WEAK_CIPHER,
)

JS_WEAK_HASH_RULE = PatternRule(
    id="js-weak-hash",
    name="Weak hash algorithm (MD5/SHA-1)",
    cwe="CWE-328",
    languages=_JS_TS,
    pattern=_JS_WEAK_HASH,
)

JS_WEAK_CIPHER_RULE = PatternRule(
    id="js-weak-cipher",
    name="Weak cipher algorithm (DES/3DES/RC4)",
    cwe="CWE-327",
    languages=_JS_TS,
    pattern=_JS_WEAK_CIPHER,
)

WEAK_CRYPTO_RULES: tuple[PatternRule, ...] = (
    PYTHON_WEAK_HASH_RULE,
    PYTHON_WEAK_CIPHER_RULE,
    JS_WEAK_HASH_RULE,
    JS_WEAK_CIPHER_RULE,
)
