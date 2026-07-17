"""Safe: a fixed dispatch table replaces dynamic evaluation (CWE-95)."""


_OPERATIONS = {"increment": lambda value: value + 1}


def apply(operation: str, value: int) -> int:
    return _OPERATIONS[operation](value)  # sast:safe
