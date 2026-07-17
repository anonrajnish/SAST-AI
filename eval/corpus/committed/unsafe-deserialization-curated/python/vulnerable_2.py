"""Unsafe deserialization: yaml.load without SafeLoader (CWE-502)."""

import yaml


def load(stream: str) -> object:
    return yaml.load(stream)  # sast:vuln
