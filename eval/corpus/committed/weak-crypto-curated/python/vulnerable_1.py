"""Weak hash: MD5 used to hash data (CWE-328)."""

import hashlib


def digest(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()  # sast:vuln
