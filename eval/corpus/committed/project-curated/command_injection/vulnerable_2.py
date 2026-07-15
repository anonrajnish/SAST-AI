"""Command injection via subprocess with shell=True (CWE-78)."""
import subprocess


def count_lines(filename: str) -> bytes:
    return subprocess.check_output(f"wc -l {filename}", shell=True)  # sast:vuln
