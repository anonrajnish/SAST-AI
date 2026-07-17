"""Safe TLS: requests keeps certificate verification enabled (CWE-295 safe)."""

import requests


def fetch(url: str) -> bytes:
    return requests.get(url, verify=True).content  # sast:safe
