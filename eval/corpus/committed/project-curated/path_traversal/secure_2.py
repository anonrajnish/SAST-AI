"""Safe file access: strip directory components with basename (CWE-22)."""
import os


def read_log(name: str) -> str:
    safe_name = os.path.basename(name)  # sast:safe
    with open(os.path.join("/var/log/app", safe_name)) as handle:
        return handle.read()
