"""Safe SQL access using a parameterized query (CWE-89)."""
import sqlite3


def find_user(conn: sqlite3.Connection, user_id: str):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))  # sast:safe
    return cursor.fetchone()
