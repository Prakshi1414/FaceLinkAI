
import os
import uuid
import shutil
import hashlib
import cv2
import numpy as np
from collections import Counter
 
from backend.embedding_store import (
    get_embedding_from_crop,
    add_embedding,
    load_db,
    rename_person,
    get_all_names,
)
from backend.faiss_index import (
    build_index,
    search_face,
    get_all_centroids,
    SIMILARITY_THRESHOLD,
    MERGE_THRESHOLD,
)
 
IMAGE_DIR = "data/images"
TEMP_DIR  = "temp"
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR,  exist_ok=True)
 
 
# ── Utilities ─────────────────────────────────────────────────────────────────
def get_image_hash(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()
 
 
def _already_in_db(name: str, image_path: str, db_records: list[dict]) -> bool:
    """FIX 5: prevent duplicate (name, image_path) rows."""
    return any(r["name"] == name and r["image"] == image_path for r in db_records)
 
 
# ── Face extraction ───────────────────────────────────────────────────────────
def extract_faces(image_path: str) -> list[dict]:
    """
    FIX 1: retinaface instead of opencv.
    Returns DeepFace face dicts with aligned numpy arrays.
    confidence < 0.85 faces are dropped to avoid blurry/partial detections.
    """
    from deepface import DeepFace
    try:
        faces = DeepFace.extract_faces(
            img_path          = image_path,
            detector_backend  = "retinaface",   # FIX 1
            enforce_detection = False,
            align             = True,            # critical for embedding consistency
        )
        # Filter low-confidence detections
        return [f for f in faces if f.get("confidence", 1.0) >= 0.85]
    except Exception as e:
        print(f"[face_engine] extract_faces error: {e}")
        return []
 
 
# ── Auto-merge duplicates ─────────────────────────────────────────────────────
def auto_merge_duplicates():
    """
    FIX 6: Compare all (person_A, person_B) centroid pairs.
    If cosine similarity > MERGE_THRESHOLD → merge smaller into larger.
    'Larger' = more DB rows (more training signal → more reliable centroid).
    """
    centroids = get_all_centroids()   # { name: np.array }
    if len(centroids) < 2:
        return
 
    db_records = load_db()
    # Count rows per person
    row_count = Counter(r["name"] for r in db_records)
 
    names   = list(centroids.keys())
    merged  = set()
    did_merge = False
 
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if a in merged or b in merged:
                continue
 
            sim = float(np.dot(centroids[a], centroids[b]))   # cosine (unit vecs)
            if sim >= MERGE_THRESHOLD:
                # keep the person with more embeddings
                keep, drop = (a, b) if row_count[a] >= row_count[b] else (b, a)
                print(f"[face_engine] Merging '{drop}' → '{keep}'  (sim={sim:.3f})")
                rename_person(drop, keep)
                merged.add(drop)
                did_merge = True
 
    if did_merge:
        build_index()
 
 
# ── Core recognition pipeline ─────────────────────────────────────────────────
def recognize_faces(image_path: str, auto_save: bool = True) -> list[dict]:
    """
    Full pipeline:
      1. Stable file copy (hash-named)
      2. Extract + align faces (retinaface)
      3. Embed each face (Facenet512, unit-normalized)
      4. Search centroid index (cosine similarity)
      5. Register new / append existing
      6. Rebuild index only if DB changed
      7. Return results
    """
    db_records = load_db()
 
    # ── Step 1: permanent storage (dedup by content hash) ────────────────────
    file_hash   = get_image_hash(image_path)
    file_ext    = os.path.splitext(image_path)[1].lower() or ".jpg"
    perm_path   = os.path.join(IMAGE_DIR, f"{file_hash}{file_ext}")
    if not os.path.exists(perm_path):
        shutil.copy(image_path, perm_path)
 
    # ── Step 2: extract faces ─────────────────────────────────────────────────
    faces = extract_faces(perm_path)
    if not faces:
        return []
 
    final_results = []
    db_changed    = False
 
    for face in faces:
        raw_crop = face.get("face")          # float32 [0,1] RGB numpy array
        if raw_crop is None or raw_crop.size == 0:
            continue
 
        # ── Step 3: embed (FIX 2: pass array directly, no JPEG save) ─────────
        # Convert [0,1] float → uint8 for DeepFace
        crop_uint8 = (raw_crop * 255).clip(0, 255).astype(np.uint8)
        emb = get_embedding_from_crop(crop_uint8)
        if emb is None:
            continue
 
        # ── Step 4: search centroids ──────────────────────────────────────────
        results  = search_face(emb)
        matched  = results[0] if results else None   # best centroid match
 
        # ── Step 5: decide identity ───────────────────────────────────────────
        if matched and matched["score"] >= SIMILARITY_THRESHOLD:
            # Known person
            name   = matched["name"]
            status = "existing"
        else:
            # Unknown → new identity (FIX 4: don't merge uncertain into wrong person)
            name   = f"user_{uuid.uuid4().hex[:6]}"
            status = "new"
 
        # ── Step 6: persist (FIX 5: duplicate guard) ─────────────────────────
        if auto_save and not _already_in_db(name, perm_path, db_records):
            add_embedding(name, emb, perm_path)
            db_records.append({"name": name, "embedding": emb, "image": perm_path})
            db_changed = True
 
        all_photos = list({r["image"] for r in db_records if r["name"] == name})
        final_results.append({
            "person":    name,
            "images":    all_photos,
            "status":    status,
            "score":     round(matched["score"], 4) if matched else 0.0,
            "embedding": emb.tolist(),
        })
 
    # ── Rebuild only when something changed (FIX 7) ───────────────────────────
    if db_changed:
        build_index()
 
    return final_results
 
 
# ── Bulk registration entry point ─────────────────────────────────────────────
def register_bulk(image_paths: list[str], name: str | None = None) -> list[dict]:
    """
    Register multiple images. If `name` is provided, all detected faces are
    registered under that name (assumes all photos are of the same person).
    After all images are processed, run auto-merge to collapse any duplicates.
    """
    db_records  = load_db()
    results     = []
    db_changed  = False
 
    for image_path in image_paths:
        file_hash = get_image_hash(image_path)
        file_ext  = os.path.splitext(image_path)[1].lower() or ".jpg"
        perm_path = os.path.join(IMAGE_DIR, f"{file_hash}{file_ext}")
        if not os.path.exists(perm_path):
            shutil.copy(image_path, perm_path)
 
        faces = extract_faces(perm_path)
        if not faces:
            results.append({"file": image_path, "status": "no_face_detected"})
            continue
 
        for face in faces:
            raw_crop = face.get("face")
            if raw_crop is None or raw_crop.size == 0:
                continue
 
            crop_uint8 = (raw_crop * 255).clip(0, 255).astype(np.uint8)
            emb = get_embedding_from_crop(crop_uint8)
            if emb is None:
                continue
 
            if name:
                # Caller supplied the name → trust it
                final_name = name
            else:
                # Auto-detect identity
                hits = search_face(emb)
                if hits and hits[0]["score"] >= SIMILARITY_THRESHOLD:
                    final_name = hits[0]["name"]
                else:
                    final_name = f"user_{uuid.uuid4().hex[:6]}"
 
            # FIX 5: duplicate guard
            if not _already_in_db(final_name, perm_path, db_records):
                add_embedding(final_name, emb, perm_path)
                db_records.append({"name": final_name, "embedding": emb, "image": perm_path})
                db_changed = True
 
            results.append({"file": image_path, "registered_as": final_name, "status": "added"})
 
    if db_changed:
        build_index()
 
    # FIX 6: merge any duplicate identities created during this batch
    auto_merge_duplicates()
 
    return results