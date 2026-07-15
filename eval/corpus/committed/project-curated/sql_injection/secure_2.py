"""Safe SQL access using named placeholders (CWE-89)."""
import sqlite3


def search_products(conn: sqlite3.Connection, name: str):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name = :name", {"name": name})  # sast:safe
    return cursor.fetchall()
