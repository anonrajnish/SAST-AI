"""Command injection via os.system with untrusted input (CWE-78)."""
import os


def ping(host: str) -> None:
    os.system("ping -c 1 " + host)  # sast:vuln
