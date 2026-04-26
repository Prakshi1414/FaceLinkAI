# app/routers/recognition.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /recognize-face
#
# Accepts a single query image (selfie / unknown face).
# Workflow:
#   1. Extract embedding from query image
#   2. Search FAISS index for nearest person (respecting similarity threshold)
#   3. Query DB for all Photos with that person_id that belong to the
#      current studio's albums (multi-tenant isolation)
#   4. Return person_id + matched photos with similarity score
#
# This endpoint is PROTECTED – the caller must be an authenticated studio user.
# For a "client-facing" public selfie search, the studio would build a thin
# public proxy that calls this endpoint using a server-side studio token.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.ml.face_engine import faiss_index, get_embedding_for_query
from app.models.models import Album, Photo, RegisterUser
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
    current_user: RegisterUser = Depends(get_current_user),
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

    # ── 2. FAISS search ───────────────────────────────────────────────────────
    person_id, similarity_score = faiss_index.search(embedding, threshold=settings.FACE_SIMILARITY_THRESHOLD)

    is_new_person = person_id is None
    matched_photos: List[RecognizedPhoto] = []

    # ── 3. DB lookup – ONLY within this studio's albums (multi-tenant) ────────
    if person_id:
        # Fetch studio album IDs first
        studio_album_ids = [
            row[0]
            for row in db.query(Album.id)
            .filter(Album.register_user_id == current_user.id)
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
                    photo_id=photo.id,
                    img_path=photo.img_path,
                    album_id=photo.album_id,
                    album_name=album_name,
                    similarity=round(similarity_score, 4),
                )
                for photo, album_name in rows
            ]

    logger.info(
        "recognize-face: studio=%s  person_id=%s  score=%.4f  matches=%d",
        current_user.id, person_id, similarity_score or 0.0, len(matched_photos),
    )
    return RecognizeResponse(
        person_id=person_id,
        is_new_person=is_new_person,
        similarity_score=round(similarity_score, 4) if similarity_score else None,
        matched_photos=matched_photos,
    )