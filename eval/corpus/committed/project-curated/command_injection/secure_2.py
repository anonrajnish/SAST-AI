"""Safe command execution: fixed argument vector, no shell interpretation (CWE-78)."""
import subprocess


def count_lines(filename: str) -> bytes:
    return subprocess.check_output(["wc", "-l", filename])  # sast:safe
