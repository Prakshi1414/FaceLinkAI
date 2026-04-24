import os
import json
import uuid
import sqlite3
import numpy as np
from deepface import DeepFace

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "facelink.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ── Model config ──────────────────────────────────────────────────────────────
MODEL_NAME       = "Facenet512"
DETECTOR_BACKEND = "retinaface"
EMBEDDING_DIM    = 512


# ── DB init ───────────────────────────────────────────────────────────────────
def init_db():
    """
    Create tables if they don't exist, then safely migrate old data.

    Schema:
      persons – one row per identity
        person_id  TEXT  PK  (UUID hex, stable forever)
        name       TEXT      (display name, changeable)
        centroid   TEXT      (L2-normalised mean embedding JSON)

      faces – one row per stored embedding
        id         INTEGER PK AUTOINCREMENT
        person_id  TEXT    FK -> persons.person_id
        name       TEXT    (mirror of persons.name; kept for backward compat)
        embedding  TEXT
        image_path TEXT
    """
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # persons table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            person_id TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            centroid  TEXT NOT NULL
        )
    """)

    # faces table (original shape — person_id added below if missing)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            embedding  TEXT    NOT NULL,
            image_path TEXT    NOT NULL
        )
    """)

    # ── Safe migration: add person_id column only if it doesn't exist yet ─────
    cur.execute("PRAGMA table_info(faces)")
    existing_cols = {row[1] for row in cur.fetchall()}
    if "person_id" not in existing_cols:
        cur.execute("ALTER TABLE faces ADD COLUMN person_id TEXT")

    conn.commit()

    # ── Backfill: faces rows with person_id IS NULL (pre-migration data) ──────
    cur.execute("SELECT DISTINCT name FROM faces WHERE person_id IS NULL")
    unmigrated_names = [r[0] for r in cur.fetchall()]

    for name in unmigrated_names:
        # Reuse existing persons row if one already exists for this name
        cur.execute("SELECT person_id FROM persons WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            pid = row[0]
        else:
            pid = uuid.uuid4().hex
            # Compute centroid from all embeddings of this name
            cur.execute(
                "SELECT embedding FROM faces WHERE name = ? AND person_id IS NULL",
                (name,)
            )
            all_embs = np.array(
                [np.array(json.loads(r[0]), dtype=np.float32) for r in cur.fetchall()],
                dtype=np.float32
            )
            mean     = all_embs.mean(axis=0)
            norm     = np.linalg.norm(mean)
            centroid = (mean / (norm + 1e-10)).tolist()
            cur.execute(
                "INSERT INTO persons (person_id, name, centroid) VALUES (?, ?, ?)",
                (pid, name, json.dumps(centroid))
            )

        cur.execute(
            "UPDATE faces SET person_id = ? WHERE name = ? AND person_id IS NULL",
            (pid, name)
        )

    conn.commit()
    conn.close()


init_db()   # always called on import – safe (IF NOT EXISTS + idempotent migration)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _normalize(emb: np.ndarray) -> np.ndarray:
    """L2-normalize so dot-product == cosine similarity."""
    norm = np.linalg.norm(emb)
    return emb / (norm + 1e-10)


def _get_or_create_person(cur: sqlite3.Cursor, name: str) -> str:
    """
    Return the person_id for `name`, creating a persons row if needed.
    Centroid is seeded with zeros and immediately overwritten by
    _recompute_centroid() in the same transaction.
    """
    cur.execute("SELECT person_id FROM persons WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    pid = uuid.uuid4().hex
    cur.execute(
        "INSERT INTO persons (person_id, name, centroid) VALUES (?, ?, ?)",
        (pid, name, json.dumps([0.0] * EMBEDDING_DIM))
    )
    return pid


def _recompute_centroid(cur: sqlite3.Cursor, person_id: str) -> None:
    """
    Recompute centroid for person_id from ALL their embeddings in faces,
    then update persons.centroid. Called inside an open transaction.
    """
    cur.execute("SELECT embedding FROM faces WHERE person_id = ?", (person_id,))
    rows = cur.fetchall()
    if not rows:
        return
    all_embs = np.array(
        [np.array(json.loads(r[0]), dtype=np.float32) for r in rows],
        dtype=np.float32
    )
    mean     = all_embs.mean(axis=0)
    norm     = np.linalg.norm(mean)
    centroid = (mean / (norm + 1e-10)).tolist()
    cur.execute(
        "UPDATE persons SET centroid = ? WHERE person_id = ?",
        (json.dumps(centroid), person_id)
    )


# ── Core embedding extraction ─────────────────────────────────────────────────
def get_embedding(image_path: str) -> np.ndarray | None:
    """
    retinaface detector, align=True, returns L2-normalized vector.
    Accepts a file path OR a numpy array (aligned face crop).
    """
    try:
        results = DeepFace.represent(
            img_path          = image_path,
            model_name        = MODEL_NAME,
            detector_backend  = DETECTOR_BACKEND,
            enforce_detection = False,
            align             = True,
        )
        raw = np.array(results[0]["embedding"], dtype=np.float32)
        return _normalize(raw)
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
            detector_backend  = "skip",
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
    """
    Insert a face embedding linked to the correct person via person_id.
      1. Look up (or create) the persons row for `name` -> person_id.
      2. Insert into faces with person_id + name columns populated.
      3. Recompute centroid from ALL embeddings for that person_id.
    """
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    emb  = embedding.tolist() if hasattr(embedding, "tolist") else embedding

    # 1. Resolve person_id
    person_id = _get_or_create_person(cur, name)

    # 2. Insert face row
    cur.execute(
        "INSERT INTO faces (person_id, name, embedding, image_path) VALUES (?, ?, ?, ?)",
        (person_id, name, json.dumps(emb), image_path)
    )

    # 3. Recompute centroid (new row already inserted, so query includes it)
    _recompute_centroid(cur, person_id)

    conn.commit()
    conn.close()


def load_db() -> list[dict]:
    """
    Returns all face rows as list of {name, embedding, image, person_id}.
    Joins faces -> persons so `name` is always the canonical value from persons.
    Signature is backward-compatible: callers only use name/embedding/image.
    """
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        SELECT COALESCE(p.name, f.name) AS name,
               f.embedding,
               f.image_path,
               f.person_id
        FROM   faces f
        LEFT JOIN persons p ON f.person_id = p.person_id
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "name":      row[0],
            "embedding": _normalize(np.array(json.loads(row[1]), dtype=np.float32)),
            "image":     row[2],
            "person_id": row[3],
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
    """
    Rename / merge a person (used after auto-merge).
    - Re-points all faces rows from old person_id -> new person_id.
    - Updates name mirror on faces rows.
    - Deletes the merged-away persons row.
    - Recomputes the winner's centroid from all combined embeddings.
    """
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("SELECT person_id FROM persons WHERE name = ?", (old_name,))
    old_row = cur.fetchone()
    cur.execute("SELECT person_id FROM persons WHERE name = ?", (new_name,))
    new_row = cur.fetchone()

    if old_row and new_row:
        old_pid = old_row[0]
        new_pid = new_row[0]
        # Re-point faces from loser -> winner
        cur.execute(
            "UPDATE faces SET person_id = ?, name = ? WHERE person_id = ?",
            (new_pid, new_name, old_pid)
        )
        # Remove the loser's persons row
        cur.execute("DELETE FROM persons WHERE person_id = ?", (old_pid,))
        # Recompute winner's centroid (now includes all merged embeddings)
        _recompute_centroid(cur, new_pid)
    else:
        # Fallback for edge cases / legacy rows without person_id
        cur.execute("UPDATE faces SET name = ? WHERE name = ?", (new_name, old_name))
        if old_row:
            cur.execute("DELETE FROM persons WHERE person_id = ?", (old_row[0],))

    conn.commit()
    conn.close()


def get_all_names() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT name FROM faces")
    names = [r[0] for r in cur.fetchall()]
    conn.close()
    return names