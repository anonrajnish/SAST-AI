"""Safe: database password read from the environment (CWE-798)."""
import os


def get_connection_string() -> str:
    password = os.environ["DB_PASSWORD"]  # sast:safe
    return f"postgresql://app:{password}@db.internal:5432/app"
