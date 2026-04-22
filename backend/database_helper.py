import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "facelink.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            embedding TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_face_to_db(name, embedding, image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Embedding list ko string mein convert karke save karein
    emb_str = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
    cursor.execute(
        "INSERT INTO faces (name, embedding, image_path) VALUES (?, ?, ?)",
        (name, emb_str, image_path)
    )
    conn.commit()
    conn.close()

def load_all_faces():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, embedding, image_path FROM faces")
    rows = cursor.fetchall()
    conn.close()
    
  
    db_data = []
    for row in rows:
        db_data.append({
            "name": row[0],
            "embedding": json.loads(row[1]),
            "image": row[2]
        })
    return db_data

if __name__ == "__main__":
    init_db()