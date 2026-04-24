
import os
import json
import sqlite3
import numpy as np
from deepface import DeepFace
 
# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "facelink.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
 
# ── Model config ──────────────────────────────────────────────────────────────
MODEL_NAME       = "Facenet512"   # FIX 1: 512-dim >> 128-dim for accuracy
DETECTOR_BACKEND = "retinaface"   # FIX 2: retinaface >> opencv for group images
EMBEDDING_DIM    = 512
 
 
# ── DB init ───────────────────────────────────────────────────────────────────
def init_db():
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
    # person_id groups multiple embeddings per person (centroid system)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            person_id TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            centroid  TEXT NOT NULL        -- L2-normalised mean embedding
        )
    """)
    conn.commit()
    conn.close()
 
 
init_db()   # always called on import – safe (IF NOT EXISTS)
 
 
# ── Helpers ───────────────────────────────────────────────────────────────────
def _normalize(emb: np.ndarray) -> np.ndarray:
    """L2-normalize so dot-product == cosine similarity."""
    norm = np.linalg.norm(emb)
    return emb / (norm + 1e-10)
 
 
# ── Core embedding extraction ─────────────────────────────────────────────────
def get_embedding(image_path: str) -> np.ndarray | None:
    """
    FIX 2 + 3:  retinaface detector, align=True, returns L2-normalized vector.
    Accepts a file path OR a numpy array (aligned face crop).
    """
    try:
        results = DeepFace.represent(
            img_path          = image_path,
            model_name        = MODEL_NAME,
            detector_backend  = DETECTOR_BACKEND,
            enforce_detection = False,
            align             = True,      # FIX 2: critical for pose consistency
        )
        raw = np.array(results[0]["embedding"], dtype=np.float32)
        return _normalize(raw)             # FIX 3: always return unit vector
    except Exception as e:
        print(f"[embedding_store] get_embedding error: {e}")
        return None
 
 
def get_embedding_from_crop(face_array: np.ndarray) -> np.ndarray | None:
    """
    For faces already cropped/aligned by DeepFace.extract_faces().
    Uses detector_backend='skip' to avoid double-detection.
    """
    try:
        results = DeepFace.represent(
            img_path          = face_array,
            model_name        = MODEL_NAME,
            detector_backend  = "skip",    # crop is already aligned
            enforce_detection = False,
            align             = False,
        )
        raw = np.array(results[0]["embedding"], dtype=np.float32)
        return _normalize(raw)
    except Exception as e:
        print(f"[embedding_store] get_embedding_from_crop error: {e}")
        return None
 
 
# ── DB read / write ───────────────────────────────────────────────────────────
def add_embedding(name: str, embedding: np.ndarray, image_path: str):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    emb  = embedding.tolist() if hasattr(embedding, "tolist") else embedding
    cur.execute(
        "INSERT INTO faces (name, embedding, image_path) VALUES (?, ?, ?)",
        (name, json.dumps(emb), image_path)
    )
    conn.commit()
    conn.close()
 
 
def load_db() -> list[dict]:
    """Returns all rows as list of {name, embedding (np.array), image}."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT name, embedding, image_path FROM faces")
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "name":      row[0],
            "embedding": _normalize(np.array(json.loads(row[1]), dtype=np.float32)),
            "image":     row[2],
        }
        for row in rows
    ]
 
 
def get_embedding_from_db(name: str) -> np.ndarray | None:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT embedding FROM faces WHERE name = ? LIMIT 1", (name,))
    row = cur.fetchone()
    conn.close()
    if row:
        return _normalize(np.array(json.loads(row[0]), dtype=np.float32))
    return None
 
 
def update_name_in_db(image_path: str, new_name: str):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("UPDATE faces SET name = ? WHERE image_path = ?", (new_name, image_path))
    conn.commit()
    conn.close()
 
 
def rename_person(old_name: str, new_name: str):
    """Rename ALL rows for a person (used after merge)."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("UPDATE faces SET name = ? WHERE name = ?", (new_name, old_name))
    conn.commit()
    conn.close()
 
 
def get_all_names() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT name FROM faces")
    names = [r[0] for r in cur.fetchall()]
    conn.close()
    return names
 