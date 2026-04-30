# app/routers/albums.py
# ─────────────────────────────────────────────────────────────────────────────
# POST   /create-album
# GET    /get-albums
# GET    /album/{id}
# POST   /album/{album_id}/generate-share-link  
# POST   /album/{album_id}/toggle-share
# GET    /album/share/{share_link}          ← PUBLIC (no auth)
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
import uuid as _uuid
from app.utils.auth import get_current_user
from app.models.models import User
from fastapi import APIRouter, Depends, HTTPException, status
from requests import request
from sqlalchemy.orm import Session
from app.schemas.schemas import ShareLinkRequest
from app.db.database import get_db
from app.models.models import Album, Photo, User
from app.schemas.schemas import (
    AlbumResponse,
    CreateAlbumRequest,
    MessageResponse,
    PhotoResponse,
    PublicAlbumResponse,
    PublicPhotoItem,
    ShareLinkResponse,
)
from app.schemas.schemas import ShareLinkRequest
from app.utils.auth import get_current_user

router = APIRouter(tags=["Albums"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_album_or_404(album_id: _uuid.UUID, user: User, db: Session):
    album = (
        db.query(Album)
        .filter(Album.id == album_id, Album.user_id == user.id)
        .first()
    )
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found.")
    return album


# ─────────────────────────────────────────────────────────────────────────────
# POST /create-album
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/create-album",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event album",
)
def create_album(
    payload: CreateAlbumRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album = Album(
    user_id=current_user.id,
    album_name=payload.album_name,
    event_date=payload.event_date,
    share_link=None,  
    is_active=False 
)
    db.add(album)
    db.commit()
    db.refresh(album)
    logger.info("Album created: %s by studio %s", album.id, current_user.id)
    return album


# ─────────────────────────────────────────────────────────────────────────────
# GET /get-albums
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/get-albums",
    response_model=list[AlbumResponse],
    summary="List all albums for the logged-in studio",
)
def get_albums(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Album)
       .filter(Album.user_id == current_user.id)
        .order_by(Album.created_at.desc())
        .all()
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /album/{id}
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/album/{album_id}",
    response_model=AlbumResponse,
    summary="Get a single album by ID",
)
def get_album(
    album_id: _uuid.UUID,
    db: Session = Depends(get_db),
   current_user: User = Depends(get_current_user)
):
    return _get_album_or_404(album_id, current_user, db)


# ─────────────────────────────────────────────────────────────────────────────
# POST /album/{album_id}/generate-share-link
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/album/generate-share-link",
    response_model=ShareLinkResponse,
    summary="Generate (or regenerate) a unique share link for an album",
)
def generate_share_link(
    request: ShareLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album_id = request.album_id
    album = _get_album_or_404(album_id, current_user, db)
    album.share_link = _uuid.uuid4().hex   # Regenerate token
    album.is_active  = True
    db.commit()
    db.refresh(album)
    return ShareLinkResponse(
        album_id=album.id,
        share_link=album.share_link,
        is_active=album.is_active,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /album/{album_id}/toggle-share
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/album/toggle-share",
    response_model=ShareLinkResponse,
    summary="Toggle album sharing on/off",
)
def toggle_share(
    request: ShareLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album_id = request.album_id 
    album = _get_album_or_404(album_id, current_user, db)
    album.is_active = not album.is_active
    db.commit()
    db.refresh(album)
    return ShareLinkResponse(
        album_id=album.id,
        share_link=album.share_link,
        is_active=album.is_active,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /album/share/{share_link}   ← PUBLIC (no auth)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/album/share/{share_link}",
    response_model=PublicAlbumResponse,
    summary="Public: view album via share link (no login required)",
)
def public_album(
    share_link: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  
):

    album = (
        db.query(Album)
        .filter(Album.share_link == share_link, Album.is_active == True)  # noqa: E712
        .first()
    )
    if not album:
        raise HTTPException(
            status_code=401,
            detail="LOGIN_REQUIRED"
        )

    photos = (
        db.query(Photo)
        .filter(Photo.album_id == album.id)
        .order_by(Photo.uploaded_at)
        .all()
    )

    return PublicAlbumResponse(
    album_id=album.id,
    album_name=album.album_name,
    event_date=album.event_date,
    total_photos=album.total_photos,
    photos=[
        PublicPhotoItem(id=p.id, img_path=p.img_path, person_id=str(p.person_id) if p.person_id else None)
        for p in photos
    ],
)
