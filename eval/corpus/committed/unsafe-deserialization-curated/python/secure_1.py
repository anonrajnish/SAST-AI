"""Safe deserialization: json.loads only parses data (CWE-502 safe)."""

import json


def load(data: str) -> object:
    return json.loads(data)  # sast:safe
