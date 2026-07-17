"""Unsafe deserialization: pickle.loads on untrusted data (CWE-502)."""

import pickle


def load(data: bytes) -> object:
    return pickle.loads(data)  # sast:vuln
