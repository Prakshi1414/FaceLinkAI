
from __future__ import annotations

import logging
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.models.models import Person
from sqlalchemy.orm import Session
import faiss
import numpy as np
import cv2
from PIL import Image as _PILImage, ImageOps as _ImageOps
import tempfile
import os



logger = logging.getLogger(__name__)

# ── Lazy model imports ────────────────────────────────────────────────────────
_deepface = None


def _get_deepface():
    global _deepface
    if _deepface is None:
        from deepface import DeepFace  # noqa: PLC0415
        _deepface = DeepFace
    return _deepface


# ── Constants ──────────────────────────────────────────────────────────────────
EMBEDDING_DIM = 512
MODEL_NAME    = "Facenet512"

# Confidence threshold for accepting a detected face.
# 0.70 is safe for studio photos (angled, group shots, etc.).
# Old broken code used 0.85 which was too aggressive.
CONFIDENCE_THRESHOLD = 0.70


# ─────────────────────────────────────────────────────────────────────────────
# In-memory FAISS store (unchanged from new backend – correct)
# ─────────────────────────────────────────────────────────────────────────────
class FAISSPersonIndex:
    """Thread-safe in-memory FAISS index storing ALL face embeddings per person."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self._person_ids: List[str] = []                    # FAISS row → person_id
        self._embeddings: Dict[str, List[np.ndarray]] = {}  # person_id → [emb1, emb2, ...]

    @staticmethod
    def _l2_norm(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def load_from_db(self, embeddings: Dict[str, List[np.ndarray]]) -> None:
        """Load ALL individual embeddings per person (not centroids)."""
        with self._lock:
            self._embeddings = {
                pid: [e.copy() for e in embs]
                for pid, embs in embeddings.items()
            }
            self._rebuild_index()
        total_emb = sum(len(v) for v in self._embeddings.values())
        logger.info(
            "FAISS index loaded: %d embeddings across %d persons.",
            total_emb, len(self._embeddings),
        )

    def _rebuild_index(self) -> None:
        self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self._person_ids = []
        for pid, emb_list in self._embeddings.items():
            for emb in emb_list:
                normed = self._l2_norm(emb).reshape(1, -1).astype("float32")
                self._index.add(normed)
                self._person_ids.append(pid)

    def search(
        self,
        embedding: np.ndarray,
        threshold: float,
    ) -> Tuple[Optional[str], float]:
        normed = self._l2_norm(embedding).reshape(1, -1).astype("float32")
        with self._lock:
            if self._index.ntotal == 0:
                return None, 0.0
            scores, indices = self._index.search(normed, k=1)
        score = float(scores[0][0])
        idx = int(indices[0][0])
        
        # ✅ NEW: Log the match score here!
        logger.info(
            "FAISS Search → Top score: %.4f (Threshold: %.2f) → Matched: %s",
            score, threshold, score >= threshold
        )

        if score >= threshold and 0 <= idx < len(self._person_ids):
            return self._person_ids[idx], score
        return None, score

    def add_embedding(self, person_id: str, embedding: np.ndarray) -> None:
        """Add a single face embedding for a person — no averaging!"""
        with self._lock:
            if person_id not in self._embeddings:
                self._embeddings[person_id] = []
            self._embeddings[person_id].append(embedding.copy())
            # Add directly to FAISS — no full rebuild needed
            normed = self._l2_norm(embedding).reshape(1, -1).astype("float32")
            self._index.add(normed)
            self._person_ids.append(person_id)

    def get_embedding_count(self, person_id: str) -> int:
        with self._lock:
            return len(self._embeddings.get(person_id, []))

    @property
    def total_persons(self) -> int:
        return len(self._embeddings)

# Module-level per-user FAISS indexes
faiss_indexes: Dict[str, FAISSPersonIndex] = {}

# Legacy single global index (kept for health endpoint compatibility)
faiss_index: FAISSPersonIndex = FAISSPersonIndex()


def get_faiss_index(user_id: str, db: Session) -> FAISSPersonIndex:
    if user_id not in faiss_indexes:
        index = FAISSPersonIndex()

        if db is not None:
            # ── Load ALL individual face embeddings from Photo table ──
            from app.models.models import Photo, Album  # avoid circular import

            photos = (
                db.query(Photo)
                .join(Album, Album.id == Photo.album_id)
                .filter(Album.user_id == user_id)
                .filter(Photo.embedding.isnot(None))
                .filter(Photo.person_id.isnot(None))
                .all()
            )

            embeddings: Dict[str, List[np.ndarray]] = {}
            for photo in photos:
                pid = str(photo.person_id)
                emb = bytes_to_embedding(photo.embedding)
                if pid not in embeddings:
                    embeddings[pid] = []
                embeddings[pid].append(emb)

            index.load_from_db(embeddings)

        faiss_indexes[user_id] = index

    return faiss_indexes[user_id]

# ─────────────────────────────────────────────────────────────────────────────
# FIX: Unified extract + embed using DeepFace.extract_faces (OLD working way)
# ─────────────────────────────────────────────────────────────────────────────

def extract_and_embed_faces(image_path: str) -> List[Tuple[np.ndarray, float]]:

    DeepFace = _get_deepface()
    results: List[Tuple[np.ndarray, float]] = []

    # ── Step 1: Detect and align all faces ────────────────────────────────────
    try:
        faces = DeepFace.extract_faces(
            img_path          = image_path,
            detector_backend  = "retinaface",
            enforce_detection = False,   # FIX BUG 3: never raise on uncertain detection
            align             = True,    # critical: aligned crops give consistent embeddings
        )
    except Exception as exc:
        logger.warning("DeepFace.extract_faces failed for %s: %s", image_path, exc)
        return []

    if not faces:
        logger.info("No faces returned by extract_faces for %s", image_path)
        return []

    # ── Step 2: Filter by confidence ──────────────────────────────────────────
    # FIX BUG 4: use 0.70 not 0.85
    valid_faces = [f for f in faces if f.get("confidence", 1.0) >= CONFIDENCE_THRESHOLD]
    if not valid_faces:
        logger.debug(
            "All %d detected faces below confidence threshold %.2f in %s",
            len(faces), CONFIDENCE_THRESHOLD, image_path,
        )
        return []

    # ── Step 3 & 4: Embed each face ───────────────────────────────────────────
    for face_dict in valid_faces:
        raw_crop = face_dict.get("face")  # float32 [0,1] RGB numpy array

        # FIX BUG 2: skip faces with missing/empty crop, don't fall back to full image
        if raw_crop is None or (hasattr(raw_crop, "size") and raw_crop.size == 0):
            logger.debug("Face crop is empty, skipping.")
            continue

        # Convert [0,1] float32 RGB → uint8 (DeepFace expects uint8 for skip backend)
        crop_uint8 = (np.array(raw_crop) * 255).clip(0, 255).astype(np.uint8)

        try:
            # FIX BUG 1 & 5: embed the aligned crop directly — no disk write,
            # no color swap, no second detection pass.
            emb_results = DeepFace.represent(
                img_path          = crop_uint8,
                model_name        = MODEL_NAME,
                detector_backend  = "skip",   # already detected & aligned above
                enforce_detection = False,
                align             = False,    # already aligned
            )
            if not emb_results:
                continue

            raw_emb = np.array(emb_results[0]["embedding"], dtype="float32")

            # L2-normalise so FAISS inner-product == cosine similarity
            norm = np.linalg.norm(raw_emb)
            if norm > 0:
                raw_emb = raw_emb / norm

            confidence = face_dict.get("confidence", 1.0)
            results.append((raw_emb, confidence))

        except Exception as exc:
            logger.warning("Embedding failed for a face crop in %s: %s", image_path, exc)
            continue

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Kept for recognition.py /recognize-face endpoint (query image path)
# ─────────────────────────────────────────────────────────────────────────────

def get_embedding_for_query(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Extract embedding from raw image bytes (used in /recognize-face endpoint).
    Saves to a temp file, uses extract_and_embed_faces, then removes it.
    Returns the embedding of the first (highest-confidence) face found.
    """

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        face_embeddings = extract_and_embed_faces(tmp_path)
        if not face_embeddings:
            return None
        # Return the first (best) face embedding
        return face_embeddings[0][0]
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Serialisation helpers (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def embedding_to_bytes(emb: np.ndarray) -> bytes:
    """Serialise float32 ndarray → bytes for DB storage."""
    return emb.astype("float32").tobytes()


def bytes_to_embedding(data: bytes) -> np.ndarray:
    """Deserialise bytes → float32 ndarray (512,)."""
    return np.frombuffer(data, dtype="float32").copy()


# ─────────────────────────────────────────────────────────────────────────────
# FIX BUG 6: process_image_for_clustering now returns ALL faces per image
# ─────────────────────────────────────────────────────────────────────────────

def process_image_for_clustering(
    image_path: str,
    user_id: str,
    album_id: str,
    threshold: float,
    db: Session,
) -> List[Tuple[Optional[str], Optional[np.ndarray], bool]]:

    face_embeddings = extract_and_embed_faces(image_path)

    if not face_embeddings:
        logger.debug("No face detected in %s", image_path)
        return []

    faiss_idx = get_faiss_index(user_id, db)
    face_results = []

    for embedding, confidence in face_embeddings:

        # 🔥 STEP 1: FAISS SEARCH (against ALL individual embeddings now!)
        matched_id, score = faiss_idx.search(embedding, threshold)

        is_new = matched_id is None

        # 🔥 STEP 2: DB LOGIC
        if matched_id is None:
            new_person = Person(
                name="Unknown",
                centroid=embedding.tolist(),
                user_id=user_id,
                album_id=album_id,
            )
            db.add(new_person)
            db.commit()
            db.refresh(new_person)
            person_id = str(new_person.person_id)

        else:
            person_id = matched_id

            # Update centroid in DB for reference (proper running average)
            person = db.query(Person).filter(Person.person_id == matched_id).first()
            if person:
                old = np.array(person.centroid)
                emb_count = faiss_idx.get_embedding_count(person_id)
                # ✅ CORRECT running average: old_mean * n + new / (n+1)
                updated = (old * emb_count + embedding) / (emb_count + 1)
                person.centroid = updated.tolist()
                db.commit()

        # 🔥 STEP 3: Add INDIVIDUAL embedding to FAISS (not centroid!)
        faiss_idx.add_embedding(person_id, embedding)

        logger.info(
            "Image %s → person_id=%s score=%.4f new=%s confidence=%.3f",
            Path(image_path).name,
            person_id,
            score,
            is_new,
            confidence,
        )
        face_results.append((person_id, embedding, is_new))

    return face_results

# ─────────────────────────────────────────────────────────────────────────────
# Legacy single-result wrapper (kept so startup.py doesn't break)
# ─────────────────────────────────────────────────────────────────────────────

def process_image_for_clustering_single(
    image_path: str,
    user_id: str,
    album_id: str,
    threshold: float,
    db: Session,
) -> Tuple[Optional[str], Optional[np.ndarray], bool]:
    """Single-face convenience wrapper."""
    results = process_image_for_clustering(
        image_path, user_id, album_id, threshold, db
    )
    if not results:
        return None, None, False
    return results[0]