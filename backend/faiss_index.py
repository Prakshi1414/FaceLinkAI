import sqlite3
import faiss
import numpy as np
import json
import os

# ── Paths (mirrors embedding_store) ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "facelink.db")

# Import load_db only for get_all_centroids (kept for face_engine compatibility)
from backend.embedding_store import load_db

# ── Module state ──────────────────────────────────────────────────────────────
_index         = None
_person_ids    = []   # position i -> person_id  (internal key)
_person_names  = []   # position i -> name        (for output)
_person_images = []   # position i -> representative image path

SIMILARITY_THRESHOLD = 0.55   # cosine similarity (unit sphere dot product)
MERGE_THRESHOLD      = 0.72   # above this -> same person, should auto-merge


# ── Centroid computation (kept for get_all_centroids / face_engine) ───────────
def _compute_centroids(db: list[dict]) -> dict[str, dict]:
    """
    Group all embeddings by name, compute L2-normalised mean (centroid).
    Returns { name: { centroid: np.array, images: [path,...] } }
    Used only by get_all_centroids() which face_engine.auto_merge_duplicates needs.
    """
    from collections import defaultdict
    groups = defaultdict(lambda: {"embeddings": [], "images": []})

    for row in db:
        name = row["name"]
        groups[name]["embeddings"].append(row["embedding"])
        groups[name]["images"].append(row["image"])

    centroids = {}
    for name, data in groups.items():
        embs     = np.array(data["embeddings"], dtype=np.float32)
        mean     = embs.mean(axis=0)
        norm     = np.linalg.norm(mean)
        centroid = mean / (norm + 1e-10)
        centroids[name] = {
            "centroid": centroid,
            "images":   list(set(data["images"]))
        }
    return centroids


# ── Build index ───────────────────────────────────────────────────────────────
def build_index():
    """
    Build a FAISS IndexFlatIP (cosine via inner product on unit vectors).
    Reads centroids directly from persons table — the authoritative source.
    Internally tracks person_id; returns name in search output.
    """
    global _index, _person_ids, _person_names, _person_images

    if not os.path.exists(DB_PATH):
        print("[faiss_index] DB not found – index not built.")
        _index = None
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Pull every person alongside one representative image from faces
    cur.execute("""
        SELECT p.person_id,
               p.name,
               p.centroid,
               (SELECT f.image_path
                FROM   faces f
                WHERE  f.person_id = p.person_id
                LIMIT  1) AS rep_image
        FROM   persons p
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("[faiss_index] persons table is empty – index not built.")
        _index = None
        return

    vectors       = []
    _person_ids   = []
    _person_names = []
    _person_images = []

    for person_id, name, centroid_json, rep_image in rows:
        centroid = np.array(json.loads(centroid_json), dtype=np.float32)
        # Skip degenerate zero centroids (seed value before first real embedding)
        if np.linalg.norm(centroid) < 1e-6:
            continue
        vectors.append(centroid)
        _person_ids.append(person_id)
        _person_names.append(name)
        _person_images.append(rep_image or "")

    if not vectors:
        print("[faiss_index] No valid centroids found – index not built.")
        _index = None
        return

    X      = np.array(vectors, dtype=np.float32)
    dim    = X.shape[1]
    _index = faiss.IndexFlatIP(dim)
    _index.add(X)
    print(f"[faiss_index] Index built: {_index.ntotal} persons indexed.")


def get_index():
    """Lazy build: ensures index is ready before any search."""
    global _index
    if _index is None:
        build_index()
    return _index


# ── Search ────────────────────────────────────────────────────────────────────
def search_face(query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
    """
    Search against person centroids.
    Internally uses person_id for position lookup; returns name in results.
    Returns list of { name, image, score } sorted by score desc.
    Only includes results above SIMILARITY_THRESHOLD.
    """
    idx = get_index()
    if idx is None or idx.ntotal == 0:
        return []

    query = query_embedding.astype(np.float32).reshape(1, -1)
    k     = min(top_k, idx.ntotal)

    scores, indices = idx.search(query, k=k)

    results = []
    for i, pos in enumerate(indices[0]):
        if pos == -1:
            continue
        score = float(scores[0][i])
        if score >= SIMILARITY_THRESHOLD:
            results.append({
                "name":      _person_names[pos],   # human-readable for callers
                "person_id": _person_ids[pos],     # available if callers want it
                "image":     _person_images[pos],
                "score":     score,
            })

    return results   # already sorted desc by FAISS


def get_all_centroids() -> dict[str, np.ndarray]:
    """
    Used by face_engine.auto_merge_duplicates() to compare centroid pairs.
    Returns { name: centroid_np_array } — same shape as before.
    """
    db = load_db()
    if not db:
        return {}
    return {name: data["centroid"] for name, data in _compute_centroids(db).items()}