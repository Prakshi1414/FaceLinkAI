# app/routers/recognition.py  (FIXED)
# ─────────────────────────────────────────────────────────────────────────────
# CHANGE: pass str(current_user.id) to get_faiss_index() consistently.
# The old broken version called get_faiss_index(str(current_user.id)) in one
# place but imported the global `faiss_index` singleton in health check.
# Now all lookups go through get_faiss_index(user_id).
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.ml.face_engine import get_faiss_index, get_embedding_for_query
from app.models.models import Album, Photo, User
from app.schemas.schemas import RecognizeResponse, RecognizedPhoto
from app.utils.auth import get_current_user

router = APIRouter(tags=["Recognition"])
logger = logging.getLogger(__name__)


@router.post(
    "/recognize-face",
    response_model=RecognizeResponse,
    summary="Upload a query face image and find all matching photos in your studio albums",
)
async def recognize_face(
    file: UploadFile = File(..., description="Query image containing one face"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── 1. Read image bytes and extract embedding ─────────────────────────────
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")

    embedding = get_embedding_for_query(image_bytes)
    if embedding is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No face detected in the uploaded image. Please use a clear frontal face photo.",
        )

    # ── 2. FAISS search (per-user index) ──────────────────────────────────────
    user_id    = str(current_user.id)
    user_index = get_faiss_index(user_id, db)

    if user_index.total_persons == 0:
        return RecognizeResponse(
            person_id        = None,
            is_new_person    = True,
            similarity_score = None,
            matched_photos   = [],
        )

    person_id, similarity_score = user_index.search(
        embedding,
        threshold=settings.FACE_SIMILARITY_THRESHOLD,
    )

    is_new_person  = person_id is None
    matched_photos: List[RecognizedPhoto] = []

    # ── 3. DB lookup – only within this studio's albums ───────────────────────
    if person_id:
        studio_album_ids = [
            row[0]
            for row in db.query(Album.id)
            .filter(Album.user_id == current_user.id)
            .all()
        ]

        if studio_album_ids:
            rows = (
                db.query(Photo, Album.album_name)
                .join(Album, Album.id == Photo.album_id)
                .filter(
                    Photo.person_id == person_id,
                    Photo.album_id.in_(studio_album_ids),
                )
                .order_by(Photo.uploaded_at.desc())
                .all()
            )
            matched_photos = [
                RecognizedPhoto(
                    photo_id   = photo.id,
                    img_path   = photo.img_path,
                    album_id   = photo.album_id,
                    album_name = album_name,
                    similarity = round(similarity_score, 4),
                )
                for photo, album_name in rows
            ]

    logger.info(
        "recognize-face: studio=%s  person_id=%s  score=%s  matches=%d",
        current_user.id,
        person_id,
        f"{similarity_score:.4f}" if similarity_score is not None else "N/A",
        len(matched_photos),
    )

    return RecognizeResponse(
        person_id        = person_id,
        is_new_person    = is_new_person,
        similarity_score = round(similarity_score, 4) if similarity_score else None,
        matched_photos   = matched_photos,
    )