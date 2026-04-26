# app/routers/gallery.py
# ─────────────────────────────────────────────────────────────────────────────
# GET /gallery
#
# Returns all albums for the authenticated studio, with each album's photos
# grouped by person_id.  Photos with no detected face are placed under a
# synthetic person_id of "__no_face__".
#
# Response shape:
# {
#   "studio_id": "...",
#   "albums": [
#     {
#       "album_id": "...",
#       "album_name": "...",
#       "event_name": "...",
#       "persons": [
#         {
#           "person_id": "uuid-string",
#           "total_photos": 12,
#           "photos": [ { id, album_id, img_path, person_id, ... }, ... ]
#         },
#         ...
#       ]
#     },
#     ...
#   ]
# }
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Album, Photo, RegisterUser
from app.schemas.schemas import (
    AlbumGallery,
    GalleryResponse,
    PersonGroup,
    PhotoResponse,
)
from app.utils.auth import get_current_user

router = APIRouter(tags=["Gallery"])
logger = logging.getLogger(__name__)

_NO_FACE_SENTINEL = "__no_face__"


@router.get(
    "/gallery",
    response_model=GalleryResponse,
    summary="Get full gallery grouped by album → person",
)
def get_gallery(
    db: Session = Depends(get_db),
    current_user: RegisterUser = Depends(get_current_user),
):
    # ── 1. Fetch all albums for this studio ───────────────────────────────────
    albums: List[Album] = (
        db.query(Album)
        .filter(Album.register_user_id == current_user.id)
        .order_by(Album.created_at.desc())
        .all()
    )

    album_galleries: List[AlbumGallery] = []

    for album in albums:
        # ── 2. Fetch all photos for this album ────────────────────────────────
        photos: List[Photo] = (
            db.query(Photo)
            .filter(Photo.album_id == album.id)
            .order_by(Photo.uploaded_at)
            .all()
        )

        # ── 3. Group by person_id ─────────────────────────────────────────────
        groups: Dict[str, List[Photo]] = defaultdict(list)
        for photo in photos:
            key = photo.person_id if photo.person_id else _NO_FACE_SENTINEL
            groups[key].append(photo)

        person_groups = [
            PersonGroup(
                person_id=pid,
                total_photos=len(group_photos),
                photos=[
                    PhotoResponse(
                        id=p.id,
                        album_id=p.album_id,
                        img_path=p.img_path,
                        person_id=p.person_id,
                        file_size=p.file_size,
                        uploaded_at=p.uploaded_at,
                    )
                    for p in group_photos
                ],
            )
            for pid, group_photos in sorted(
                groups.items(),
                key=lambda kv: len(kv[1]),   # sort by descending group size
                reverse=True,
            )
        ]

        album_galleries.append(
            AlbumGallery(
                album_id=album.id,
                album_name=album.album_name,
                event_name=album.event_name,
                persons=person_groups,
            )
        )

    logger.debug(
        "Gallery fetched for studio %s: %d albums", current_user.id, len(album_galleries)
    )
    return GalleryResponse(studio_id=current_user.id, albums=album_galleries)