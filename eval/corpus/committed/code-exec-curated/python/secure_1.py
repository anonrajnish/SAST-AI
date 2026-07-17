"""Safe: ast.literal_eval parses a literal without executing code (CWE-95)."""

import ast


def compute(expression: str) -> object:
    return ast.literal_eval(expression)  # sast:safe
