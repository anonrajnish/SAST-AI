"""TLS verification disabled: requests called with verify=False (CWE-295)."""

import requests


def fetch(url: str) -> bytes:
    return requests.get(url, verify=False).content  # sast:vuln
