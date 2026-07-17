"""Dynamic code execution: eval on caller-supplied input (CWE-95)."""


def compute(expression: str) -> object:
    return eval(expression)  # sast:vuln
