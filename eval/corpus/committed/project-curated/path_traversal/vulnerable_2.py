"""Path traversal via direct concatenation into a file path (CWE-22)."""


def read_log(name: str) -> str:
    with open("/var/log/app/" + name) as handle:  # sast:vuln
        return handle.read()
