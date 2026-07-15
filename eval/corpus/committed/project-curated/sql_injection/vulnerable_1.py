"""SQL injection through string formatting (CWE-89)."""
import sqlite3


def find_user(conn: sqlite3.Connection, user_id: str):
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = '%s'" % user_id  # sast:vuln
    cursor.execute(query)
    return cursor.fetchone()
