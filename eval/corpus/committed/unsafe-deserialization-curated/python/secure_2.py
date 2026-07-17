"""Safe deserialization: yaml.safe_load restricts object construction (CWE-502 safe)."""

import yaml


def load(stream: str) -> object:
    return yaml.safe_load(stream)  # sast:safe
