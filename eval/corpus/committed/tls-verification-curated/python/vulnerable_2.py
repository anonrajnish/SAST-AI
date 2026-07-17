"""TLS verification disabled: unverified SSL context (CWE-295)."""

import ssl


def context() -> ssl.SSLContext:
    return ssl._create_unverified_context()  # sast:vuln
