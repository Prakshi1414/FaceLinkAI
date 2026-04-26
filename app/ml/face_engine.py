# app/ml/face_engine.py
# ─────────────────────────────────────────────────────────────────────────────
# FaceLinkAI – Core AI / ML Engine
#
# Responsibilities:
#   1. Face detection      → RetinaFace
#   2. Embedding           → DeepFace (Facenet512, 512-dim float32)
#   3. L2 normalisation    → numpy
#   4. Similarity search   → FAISS IndexFlatIP  (cosine similarity after L2 norm)
#   5. Person clustering   → one centroid per person_id, updated dynamically
#   6. Global person store → shared across all tenants' albums (person_id is universal)
#
# Design decisions
# ────────────────
# • FAISS index lives IN MEMORY and is rebuilt from DB centroids on startup.
#   For very large deployments, swap the in-memory store for a persisted
#   FAISS index file or a dedicated vector DB (e.g. pgvector, Weaviate).
# • person_id is a plain UUID string.  The mapping centroid_store keeps one
#   float32 centroid per person, used to update the FAISS index incrementally.
# • Thread safety: a threading.Lock guards all FAISS mutations.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import io
import logging
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Lazy imports for heavy models – imported the first time they are needed.
_deepface = None
_retinaface = None


def _get_deepface():
    global _deepface
    if _deepface is None:
        from deepface import DeepFace  # noqa: PLC0415
        _deepface = DeepFace
    return _deepface


def _get_retinaface():
    global _retinaface
    if _retinaface is None:
        from retinaface import RetinaFace  # noqa: PLC0415
        _retinaface = RetinaFace
    return _retinaface


# ── Constants ──────────────────────────────────────────────────────────────────
EMBEDDING_DIM = 512          # Facenet512 output dimensionality
MODEL_NAME    = "Facenet512"
DETECTOR      = "retinaface"


# ─────────────────────────────────────────────────────────────────────────────
# In-memory FAISS store (singleton, initialised once at startup)
# ─────────────────────────────────────────────────────────────────────────────
class FAISSPersonIndex:
    """Thread-safe in-memory FAISS index mapping centroids → person_ids."""

    def __init__(self) -> None:
        self._lock  = threading.Lock()
        self._index = faiss.IndexFlatIP(EMBEDDING_DIM)   # inner-product = cosine after L2 norm
        # person_id list: position i in this list corresponds to FAISS vector i
        self._person_ids: List[str] = []
        # centroid store: person_id → mean embedding (float32, shape (512,))
        self._centroids: Dict[str, np.ndarray] = {}

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _l2_norm(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def _rebuild_index(self) -> None:
        """Rebuild FAISS index from current centroid store (called under lock)."""
        self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self._person_ids = []
        for pid, centroid in self._centroids.items():
            normed = self._l2_norm(centroid).reshape(1, -1).astype("float32")
            self._index.add(normed)
            self._person_ids.append(pid)

    # ── Public API ────────────────────────────────────────────────────────────
    def load_from_db(self, centroids: Dict[str, np.ndarray]) -> None:
        """Bulk-load centroids from the database on application startup."""
        with self._lock:
            self._centroids = {pid: arr.copy() for pid, arr in centroids.items()}
            self._rebuild_index()
        logger.info("FAISS index loaded with %d persons.", len(self._centroids))

    def search(
        self,
        embedding: np.ndarray,
        threshold: float,
    ) -> Tuple[Optional[str], float]:
        """
        Find the nearest person whose centroid similarity ≥ threshold.

        Returns
        -------
        (person_id, similarity_score) if a match is found, else (None, best_score).
        """
        normed = self._l2_norm(embedding).reshape(1, -1).astype("float32")
        with self._lock:
            if self._index.ntotal == 0:
                return None, 0.0
            scores, indices = self._index.search(normed, k=1)
        score = float(scores[0][0])
        idx   = int(indices[0][0])
        if score >= threshold and 0 <= idx < len(self._person_ids):
            return self._person_ids[idx], score
        return None, score

    def add_or_update(self, person_id: str, embedding: np.ndarray) -> None:
        """
        Add a new person or update an existing one's centroid (rolling mean).
        Rebuilds the FAISS index after mutation.
        """
        with self._lock:
            if person_id in self._centroids:
                # Running average to keep centroid stable without storing all embeddings
                old = self._centroids[person_id]
                self._centroids[person_id] = (old + embedding) / 2.0
            else:
                self._centroids[person_id] = embedding.copy()
            self._rebuild_index()

    @property
    def total_persons(self) -> int:
        return len(self._centroids)


# Module-level singleton
faiss_index = FAISSPersonIndex()


# ─────────────────────────────────────────────────────────────────────────────
# Face detection & embedding helpers
# ─────────────────────────────────────────────────────────────────────────────

def detect_faces(image_path: str) -> List[dict]:
    """
    Run RetinaFace detection on an image file.

    Returns a list of face dicts as returned by RetinaFace.detect_faces().
    Returns empty list when no faces are found or the call fails.
    """
    try:
        RetinaFace = _get_retinaface()
        faces = RetinaFace.detect_faces(image_path)
        if isinstance(faces, dict):
            return list(faces.values())
        return []
    except Exception as exc:
        logger.warning("RetinaFace detection failed for %s: %s", image_path, exc)
        return []


def extract_embedding(image_path: str) -> Optional[np.ndarray]:
    """
    Extract a Facenet512 embedding for the first (primary) face in the image.

    Returns
    -------
    float32 ndarray of shape (512,) or None if no face is found.
    """
    try:
        DeepFace = _get_deepface()
        result = DeepFace.represent(
            img_path=image_path,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR,
            enforce_detection=True,
            align=True,
        )
        if not result:
            return None
        emb = np.array(result[0]["embedding"], dtype="float32")
        return emb
    except Exception as exc:
        logger.warning("DeepFace embedding failed for %s: %s", image_path, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Serialisation helpers for storing embeddings in PostgreSQL (LargeBinary)
# ─────────────────────────────────────────────────────────────────────────────

def embedding_to_bytes(emb: np.ndarray) -> bytes:
    """Serialise float32 ndarray → bytes for DB storage."""
    return emb.astype("float32").tobytes()


def bytes_to_embedding(data: bytes) -> np.ndarray:
    """Deserialise bytes → float32 ndarray (512,)."""
    return np.frombuffer(data, dtype="float32").copy()


# ─────────────────────────────────────────────────────────────────────────────
# High-level processing function
# ─────────────────────────────────────────────────────────────────────────────

def process_image_for_clustering(
    image_path: str,
    threshold: float,
) -> Tuple[Optional[str], Optional[np.ndarray], bool]:
    """
    Full pipeline for a single image:
      1. Detect faces (RetinaFace)
      2. Extract embedding (DeepFace Facenet512)
      3. Search FAISS for nearest centroid
      4. Assign existing person_id OR create new one
      5. Update centroid in FAISS

    Returns
    -------
    (person_id, embedding, is_new_person)
    Returns (None, None, False) when no face is detected.
    """
    # Step 1: Detect
    faces = detect_faces(image_path)
    if not faces:
        logger.debug("No face detected in %s", image_path)
        return None, None, False

    # Step 2: Embed (primary face only)
    embedding = extract_embedding(image_path)
    if embedding is None:
        return None, None, False

    # Step 3: Search
    matched_id, score = faiss_index.search(embedding, threshold)

    # Step 4: Assign
    is_new = matched_id is None
    person_id = matched_id if matched_id else str(uuid.uuid4())

    # Step 5: Update centroid
    faiss_index.add_or_update(person_id, embedding)

    logger.debug(
        "Image %s → person_id=%s  score=%.4f  new=%s",
        Path(image_path).name, person_id, score, is_new,
    )
    return person_id, embedding, is_new


def get_embedding_for_query(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Extract embedding from raw image bytes (used in /recognize-face endpoint).
    Saves to a temp file, embeds, then removes it.
    """
    import tempfile, os  # noqa: E401

    suffix = ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        return extract_embedding(tmp_path)
    finally:
        os.unlink(tmp_path)