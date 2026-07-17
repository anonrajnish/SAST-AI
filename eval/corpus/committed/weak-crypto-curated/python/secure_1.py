"""Safe: SHA-256 used to hash data (CWE-328)."""

import hashlib


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()  # sast:safe
