 
import faiss
import numpy as np
from backend.embedding_store import load_db
 
# ── Module state ──────────────────────────────────────────────────────────────
_index        = None
_person_names = []   # parallel list: position i → person name
_person_images= []   # representative image path for that person
 
SIMILARITY_THRESHOLD = 0.55   # cosine similarity (unit sphere dot product)
MERGE_THRESHOLD      = 0.72   # above this → same person, should auto-merge
 
 
# ── Centroid computation ──────────────────────────────────────────────────────
def _compute_centroids(db: list[dict]) -> dict[str, dict]:
    """
    Group all embeddings by name, compute L2-normalised mean (centroid).
    Returns { name: { centroid: np.array, images: [path,...] } }
    """
    from collections import defaultdict
    groups = defaultdict(lambda: {"embeddings": [], "images": []})
 
    for row in db:
        name = row["name"]
        groups[name]["embeddings"].append(row["embedding"])
        groups[name]["images"].append(row["image"])
 
    centroids = {}
    for name, data in groups.items():
        embs   = np.array(data["embeddings"], dtype=np.float32)
        mean   = embs.mean(axis=0)
        norm   = np.linalg.norm(mean)
        centroid = mean / (norm + 1e-10)
        centroids[name] = {
            "centroid": centroid,
            "images":   list(set(data["images"]))   # deduplicated
        }
    return centroids
 
 
# ── Build index ───────────────────────────────────────────────────────────────
def build_index():
    """
    FIX 1: One centroid per person, not one vector per image.
    Uses IndexFlatIP (inner product = cosine on unit vectors).
    """
    global _index, _person_names, _person_images
 
    db = load_db()
    if not db:
        print("[faiss_index] DB is empty – index not built.")
        _index = None
        return
 
    centroids = _compute_centroids(db)
 
    vectors       = []
    _person_names  = []
    _person_images = []
 
    for name, data in centroids.items():
        vectors.append(data["centroid"])
        _person_names.append(name)
        _person_images.append(data["images"][0])   # one representative image
 
    X = np.array(vectors, dtype=np.float32)
    # Embeddings are already unit vectors from embedding_store – no re-normalize needed.
 
    dim    = X.shape[1]
    _index = faiss.IndexFlatIP(dim)   # cosine similarity via inner product
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
    Returns list of { name, image, score } sorted by score desc.
    Only includes results above SIMILARITY_THRESHOLD.
    
    FIX 3: no faiss.normalize_L2 here – embedding_store guarantees unit vectors.
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
                "name":  _person_names[pos],
                "image": _person_images[pos],
                "score": score
            })
 
    return results   # already sorted desc by FAISS
 
 
def get_all_centroids() -> dict[str, np.ndarray]:
    """Used by auto-merge to compare centroid pairs."""
    db = load_db()
    if not db:
        return {}
    return {name: data["centroid"] for name, data in _compute_centroids(db).items()}