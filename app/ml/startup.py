# app/ml/startup.py  (FIXED)
# ─────────────────────────────────────────────────────────────────────────────
# CHANGES
# ────────
# The old broken version had a scoping bug:
#   for user_id, persons in buckets.items():
#       centroids = { ... }   ← computed inside loop
#   faiss_index.load_from_db(centroids)  ← OUTSIDE loop!
#
# This meant only the LAST user's centroids were loaded into the index,
# and load_from_db was called on the legacy global `faiss_index` singleton
# instead of the per-user index from get_faiss_index(user_id).
#
# FIX: Move load_from_db() call INSIDE the loop and use get_faiss_index(user_id).
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict

import numpy as np
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.ml.face_engine import bytes_to_embedding, get_faiss_index
from app.models.models import Photo

logger = logging.getLogger(__name__)


def bootstrap_faiss_from_db() -> None:
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(Photo.user_id, Photo.person_id, Photo.embedding)
            .filter(Photo.person_id.isnot(None), Photo.embedding.isnot(None))
            .all()
        )
    finally:
        db.close()

    if not rows:
        logger.info("No embeddings found in DB – FAISS index will be empty until first upload.")
        return

    # Group embeddings by user_id → person_id
    buckets: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    for user_id, person_id, emb_bytes in rows:
        try:
            emb = bytes_to_embedding(emb_bytes)
            buckets[str(user_id)][person_id].append(emb)
        except Exception as e:
            logger.warning("Could not deserialise embedding for person %s: %s", person_id, e)

    total_users   = 0
    total_persons = 0

    # FIX: iterate ALL users and load into THEIR per-user index
    for user_id, persons in buckets.items():
        centroids = {
            pid: np.mean(np.stack(embs), axis=0).astype("float32")
            for pid, embs in persons.items()
        }

        # FIX: use per-user index, not global singleton
        user_faiss_index = get_faiss_index(user_id)
        user_faiss_index.load_from_db(centroids)

        total_users   += 1
        total_persons += len(centroids)
        logger.info(
            "FAISS bootstrap: user=%s  persons=%d",
            user_id, len(centroids),
        )

    logger.info(
        "FAISS bootstrap complete: %d user(s), %d total persons indexed.",
        total_users, total_persons,
    )