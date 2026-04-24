
import os
import json
import sqlite3
import numpy as np
 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "facelink.db")
 
 
def init_db():
    """Create tables if they don't exist. Safe to call multiple times."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            embedding  TEXT    NOT NULL,
            image_path TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()
 
 
def load_all_faces() -> list[dict]:
    """Returns all rows. Used by gallery endpoint."""
    if not os.path.exists(DB_PATH):
        init_db()
        return []
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT name, embedding, image_path FROM faces")
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "name":      row[0],
            "embedding": json.loads(row[1]),
            "image":     row[2],
        }
        for row in rows
    ]
 
 
if __name__ == "__main__":
    init_db()
    print("DB initialized at:", DB_PATH)