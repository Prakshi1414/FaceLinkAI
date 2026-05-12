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

from fastapi import APIRouter, Depends, File,Form ,  HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import uuid as _uuid
from app.config import settings
from app.db.database import get_db
from app.ml.face_engine import get_faiss_index, get_embedding_for_query
from app.models.models import Album, Photo, User , AlbumInvite
from app.schemas.schemas import RecognizeResponse, RecognizedPhoto , ApiResponse
from app.utils.auth import get_current_user

router = APIRouter(tags=["Recognition"])
logger = logging.getLogger(__name__)


@router.post(
    "/recognize-face",
    response_model=ApiResponse[RecognizeResponse],
    summary="Upload a query face image and find all matching photos in your studio albums",
)
async def recognize_face(
    album_id: _uuid.UUID = Form(...),
    file: UploadFile = File(..., description="Query image containing one face"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── 1. Read image bytes and extract embedding ─────────────────────────────
    image_bytes = await file.read()
    if not image_bytes:
         return {
            "status": False,
            "message": "Empty file",
            "data": None
        }

    embedding = get_embedding_for_query(image_bytes)
    if embedding is None:
        return {
            "status": False,
            "message": "No face detected. Please upload a clear frontal face image",
            "data": None
        }

    # ── 2. FAISS search (per-user index) ──────────────────────────────────────



    # FIX: Always use the album_id from the request instead of guessing with .first()
    album = db.query(Album).filter(Album.id == album_id).first()
    
    if not album:
        return {
            "status": False,
            "message": "Album not found",
            "data": None
        }

    # Verify the current user has permission to access this specific album
    has_access = False
    if current_user.role == "studio":
        if album.user_id == current_user.id:
            has_access = True
    else:
        # Client or Relative access check
        if album.owner_id == current_user.id:
            has_access = True
        
        if not has_access:
            invite = (
                db.query(AlbumInvite)
                .filter(
                    AlbumInvite.album_id == album_id,
                    AlbumInvite.requested_user_id == current_user.id,
                    AlbumInvite.status == "approved",
                    AlbumInvite.is_active == True
                )
                .first()
            )
            if invite:
                has_access = True

    if not has_access:
        return {
            "status": False,
            "message": "You do not have access to this album",
            "data": None
        }
    # IMPORTANT:
    # Always use studio owner's FAISS index

    studio_owner_id = str(album.user_id)

    user_index = get_faiss_index(studio_owner_id, db)

    if user_index.total_persons == 0:
        return {
            "status": True,
            "message": "No known persons in system",
            "data": {
                "person_id": None,
                "is_new_person": True,
                "similarity_score": None,
                "matched_photos": []
            }
        }
    
    candidates = user_index.search(
        embedding,
        threshold=settings.FACE_SIMILARITY_THRESHOLD,
    )

    matched_photos: List[RecognizedPhoto] = []

    person_id = None
    similarity_score = None

    # ── 3. Find best candidate inside this album ──────────────────────────────

    for candidate_person_id, candidate_score in candidates:

        rows = (
            db.query(Photo, Album.album_name)
            .join(Album, Album.id == Photo.album_id)
            .filter(
                Photo.person_id == candidate_person_id,
                Photo.album_id == album_id,
            )
            .order_by(Photo.uploaded_at.desc())
            .all()
        )

        if rows:

            person_id = candidate_person_id
            similarity_score = candidate_score

            matched_photos = [
                RecognizedPhoto(
                    photo_id   = photo.id,
                    img_path   = photo.img_path,
                    album_id   = photo.album_id,
                    album_name = album_name,
                    similarity = round(candidate_score, 4),
                )
                for photo, album_name in rows
            ]

            break

    is_new_person = person_id is None
    return {
        "status": True,
        "message": "Face recognition completed",
        "data": {
            "person_id": person_id,
            "is_new_person": is_new_person,
            "similarity_score": round(similarity_score, 4) if similarity_score else None,
            "matched_photos": matched_photos
        }
    }