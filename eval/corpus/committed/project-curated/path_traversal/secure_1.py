"""Safe file access: resolved path confined to a base directory (CWE-22)."""
import os


def read_upload(filename: str) -> str:
    base = "/var/www/uploads"
    path = os.path.realpath(os.path.join(base, filename))
    if not path.startswith(base + os.sep):  # sast:safe
        raise ValueError("path traversal detected")
    with open(path) as handle:
        return handle.read()
