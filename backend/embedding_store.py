import os
import json
import sqlite3
from deepface import DeepFace
import numpy as np


DB_PATH = "data/facelink.db"
if not os.path.exists("data"):
    os.makedirs("data")

# --- 1. Database ko initialize karna (Table banana) ---
def init_db():
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

# --- 2. load_db() ko update karein ---
def load_db():
    if not os.path.exists(DB_PATH):
        init_db()
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, embedding, image_path FROM faces")
    rows = cursor.fetchall()
    conn.close()
    
    db_data = []
    for row in rows:
        # String embedding ko wapis Numpy Array mein badalna zaroori hai
        emb_list = json.loads(row[1])
        db_data.append({
            "name": row[0],
            "embedding": np.array(emb_list),
            "image": row[2]
        })
    return db_data

# --- Ye AI se embedding nikalne ke liye hai ---
def get_embedding(image_path):
    try:
        # DeepFace yahan use ho raha hai
        results = DeepFace.represent(
            img_path=image_path, 
            model_name="Facenet", 
            enforce_detection=False
        )
        return results[0]["embedding"]
    except Exception as e:
        print(f"DeepFace Error: {e}")
        return None
    
# --- 3. add_embedding() ko update karein ---
def add_embedding(name, embedding, image_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Embedding (Numpy Array) ko JSON string mein badlein taaki DB mein save ho sake
    emb_str = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
    
    cursor.execute(
        "INSERT INTO faces (name, embedding, image_path) VALUES (?, ?, ?)",
        (name, emb_str, image_path)
    )
    conn.commit()
    conn.close()


def get_embedding_from_db(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT embedding FROM faces WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return np.array(json.loads(row[0]))
    return None

def update_name_in_db(image_path, new_name):
    conn = sqlite3.connect(DB_PATH) # Apne DB ka naam confirm kar lein
    cursor = conn.cursor()
    cursor.execute("UPDATE faces SET name = ? WHERE image_path = ?", (new_name, image_path))
    conn.commit()
    conn.close()



