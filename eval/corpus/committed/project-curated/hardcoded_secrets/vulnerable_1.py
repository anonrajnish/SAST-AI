"""Hardcoded database credentials in source (CWE-798)."""


def get_connection_string() -> str:
    password = "S3cr3t-Example-Pw"  # sast:vuln
    return f"postgresql://app:{password}@db.internal:5432/app"
