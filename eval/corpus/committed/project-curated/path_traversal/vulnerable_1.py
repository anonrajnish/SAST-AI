"""Path traversal: untrusted filename joined without validation (CWE-22)."""
import os


def read_upload(filename: str) -> str:
    path = os.path.join("/var/www/uploads", filename)  # sast:vuln
    with open(path) as handle:
        return handle.read()
