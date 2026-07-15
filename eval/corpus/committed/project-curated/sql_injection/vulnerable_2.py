"""SQL injection through f-string concatenation (CWE-89)."""
import sqlite3


def search_products(conn: sqlite3.Connection, name: str):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM products WHERE name = '{name}'")  # sast:vuln
    return cursor.fetchall()
