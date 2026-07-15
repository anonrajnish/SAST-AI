"""Safe command execution using an argument list without a shell (CWE-78)."""
import subprocess


def ping(host: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["ping", "-c", "1", host], check=False)  # sast:safe
