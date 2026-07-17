"""Safe TLS: default SSL context verifies certificates (CWE-295 safe)."""

import ssl


def context() -> ssl.SSLContext:
    return ssl.create_default_context()  # sast:safe
