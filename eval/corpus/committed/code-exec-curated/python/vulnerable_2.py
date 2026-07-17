"""Dynamic code execution: exec of caller-supplied code (CWE-95)."""


def run(code: str) -> None:
    exec(code)  # sast:vuln
