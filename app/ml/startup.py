# app/schemas/schemas.py
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
        logger.info("No embeddings found")
        return

    buckets: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    for user_id, person_id, emb_bytes in rows:
        try:
            emb = bytes_to_embedding(emb_bytes)
            buckets[user_id][person_id].append(emb)
        except Exception as e:
            logger.warning(f"Embedding error: {e}")

    for user_id, persons in buckets.items():

        centroids = {
            pid: np.mean(np.stack(embs), axis=0).astype("float32")
            for pid, embs in persons.items()
        }

    faiss_index = get_faiss_index(user_id)
    faiss_index.load_from_db(centroids)

    logger.info(f"FAISS loaded: {len(centroids)} persons")