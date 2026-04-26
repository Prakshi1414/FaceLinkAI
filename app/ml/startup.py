# app/schemas/schemas.py
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict

import numpy as np
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.ml.face_engine import bytes_to_embedding, faiss_index
from app.models.models import Photo

logger = logging.getLogger(__name__)


def bootstrap_faiss_from_db() -> None:
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(Photo.person_id, Photo.embedding)
            .filter(Photo.person_id.isnot(None), Photo.embedding.isnot(None))
            .all()
        )
    finally:
        db.close()

    if not rows:
        logger.info("No embeddings found")
        return

    buckets: Dict[str, list] = defaultdict(list)

    for person_id, emb_bytes in rows:
        try:
            emb = bytes_to_embedding(emb_bytes)
            buckets[person_id].append(emb)
        except Exception as e:
            logger.warning(f"Embedding error: {e}")

    centroids = {
        pid: np.mean(np.stack(embs), axis=0).astype("float32")
        for pid, embs in buckets.items()
    }

    faiss_index.load_from_db(centroids)

    logger.info(f"FAISS loaded: {len(centroids)} persons")