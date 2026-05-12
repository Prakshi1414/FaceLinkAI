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
from sqlalchemy import func
from app.utils.code_generator import generate_unique_album_code
from app.utils.auth import get_current_user , hash_password
from fastapi import APIRouter, Depends, HTTPException, status
from requests import request
from sqlalchemy.orm import Session
from app.schemas.schemas import ShareLinkRequest
from app.db.database import get_db
from app.models.models import Album, Photo, User ,AlbumInvite
from app.schemas.schemas import (
    ApiResponse,
    AlbumResponse,
    CreateAlbumRequest,
    MessageResponse,
    PhotoResponse,
    PublicAlbumResponse,
    PublicPhotoItem,
    ShareLinkResponse,
    JoinAlbumRequest,
    JoinRequestListResponse,
    JoinRequestAction,
    AlbumPhotosResponse
)

router = APIRouter(tags=["Albums"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_album_or_404(album_id: _uuid.UUID, user: User, db: Session):
    return (
        db.query(Album)
        .filter(Album.id == album_id, Album.user_id == user.id)
        .first()
    )
# ─────────────────────────────────────────────────────────────────────────────
# POST /create-album
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/create-album",
    response_model=ApiResponse[AlbumResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event album",
)
def create_album(
    payload: CreateAlbumRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    client_user = db.query(User).filter(
        User.mobile_number == payload.client_mobile
    ).first()

 
    if not client_user:
        client_user = User(
            studio_name=None,
            mobile_number=payload.client_mobile,
            username=payload.client_name,
            password_hash=hash_password("123456"),
            role="client"
        )

    db.add(client_user)
    db.commit()
    db.refresh(client_user)

    album_code = generate_unique_album_code(db)

    album = Album(
        user_id=current_user.id,
        owner_id=client_user.id,

        album_name=payload.album_name,
        event_date=payload.event_date,

        album_code=album_code,

        share_link=None,
        is_active=False
    )

    db.add(album)
    db.commit()
    db.refresh(album)

    logger.info("Album created: %s by studio %s", album.id, current_user.id)

    return {
        "status": True,
        "message": "Album created successfully",
        "data": {
            "id": album.id,
            "album_name": album.album_name,
            "album_code": album.album_code,
            "event_date": album.event_date,
            "total_photos": album.total_photos,
            "total_size": album.total_size,
            "share_link": album.share_link,
            "is_active": album.is_active,
            "created_at": album.created_at,
            "photos": []   
        }
    }

# ─────────────────────────────────────────────────────────────────────────────
# GET /album/{album_id}/photos
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/album/{album_id}/photos",
    response_model=ApiResponse[AlbumPhotosResponse],
    summary="Get photos of an album",
)
def get_album_photos(
    album_id: _uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Find album
    album = (
        db.query(Album)
        .filter(Album.id == album_id)
        .first()
    )

    if not album:
        return {
            "status": False,
            "message": "Album not found",
            "data": None
        }

    # Access control

    has_access = False

    # Studio owner
    if album.user_id == current_user.id:
        has_access = True

    # Album owner/client
    elif album.owner_id == current_user.id:
        has_access = True

    else:

        # Approved relative
        approved_request = (
            db.query(AlbumInvite)
            .filter(
                AlbumInvite.album_id == album.id,
                AlbumInvite.requested_user_id == current_user.id,
                AlbumInvite.status == "approved",
                AlbumInvite.is_active == True
            )
            .first()
        )

        if approved_request:
            has_access = True

    if not has_access:
        return {
            "status": False,
            "message": "You do not have access to this album",
            "data": None
        }

    # Fetch photos
    photos = (
        db.query(Photo)
        .filter(Photo.album_id == album.id)
        .order_by(Photo.img_path, Photo.uploaded_at.desc())
        .distinct(Photo.img_path)
        .all()
    )

    return {
        "status": True,
        "message": "Album photos fetched successfully",
        "data": {
            "photos": [
                PhotoResponse.model_validate(photo)
                for photo in photos
            ]
        }
    }

# ─────────────────────────────────────────────────────────────────────────────
# GET /my-albums
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/my-albums",
    response_model=ApiResponse[list[AlbumResponse]],
    summary="Get albums owned or shared with current user",
)
def get_my_albums(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Albums owned by current user
    owned_albums = (
        db.query(Album)
        .filter(
            Album.owner_id == current_user.id
        )
        .all()
    )

    # Approved shared albums
    shared_albums = (
        db.query(Album)
        .join(
            AlbumInvite,
            Album.id == AlbumInvite.album_id
        )
        .filter(
            AlbumInvite.requested_user_id == current_user.id,
            AlbumInvite.status == "approved",
            AlbumInvite.is_active == True
        )
        .all()
    )

    # Merge both lists
    all_albums = {album.id: album for album in owned_albums}

    for album in shared_albums:
        all_albums[album.id] = album

    albums = list(all_albums.values())

    albums.sort(
        key=lambda x: x.created_at,
        reverse=True
    )

    return {
        "status": True,
        "message": "My albums fetched successfully",
        "data": [
            {
                "id": album.id,
                "album_name": album.album_name,
                "album_code": album.album_code,
                "event_date": album.event_date,
                "total_photos": (
                    db.query(Photo.img_path)
                    .filter(Photo.album_id == album.id)
                    .distinct()
                    .count()
                ),
                "share_link": album.share_link,
                "is_active": album.is_active,
                "created_at": album.created_at,
                "photos": []
            }
            for album in albums
        ]
    }

# ─────────────────────────────────────────────────────────────────────────────
# GET /get-albums
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/get-albums",
    response_model=ApiResponse[list[AlbumResponse]],
    summary="List all albums for the logged-in studio",
)
def get_albums(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    albums = (
        db.query(Album)
       .filter(Album.user_id == current_user.id)
        .order_by(Album.created_at.desc())
        .all()
    )
    album_list = [
        {
            "id": a.id,
            "album_name": a.album_name,
            "album_code": a.album_code,
            "event_date": a.event_date,
            "total_photos": (
                db.query(Photo.img_path)
                .filter(Photo.album_id == a.id)
                .distinct()
                .count()
            ),
            "total_size": (
                db.query(func.coalesce(func.sum(Photo.file_size), 0))
                .filter(Photo.album_id == a.id)
                
                .scalar()
            ),
            "share_link": a.share_link,
            "is_active": a.is_active,
            "created_at": a.created_at,
            "photos": []   
        }
        for a in albums
    ]

    return {
        "status": True,
        "message": "Albums fetched successfully",
        "data": album_list
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /album/request-action
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/request-action",
    response_model=ApiResponse[MessageResponse],
    summary="Approve or reject album join request",
)
def request_action(
    payload: JoinRequestAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    request_item = (
        db.query(AlbumInvite)
        .join(Album, Album.id == AlbumInvite.album_id)
        .filter(
            AlbumInvite.id == payload.request_id,
            Album.owner_id == current_user.id
        )
        .first()
    )

    if not request_item:
        return {
            "status": False,
            "message": "Request not found",
            "data": None
        }

    if not request_item.is_active:
        return {
            "status": False,
            "message": "Request already inactive",
            "data": None
        }

    # Update request status
    request_item.status = payload.action

    # Optional:
    # deactivate rejected requests
    if payload.action == "rejected":
        request_item.is_active = False

    db.commit()

    return {
        "status": True,
        "message": f"Request {payload.action} successfully",
        "data": {
            "message": f"Album join request {payload.action}"
        }
    }



# ─────────────────────────────────────────────────────────────────────────────
# GET /album/join-requests
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/album/join-requests",
    response_model=ApiResponse[JoinRequestListResponse],
    summary="Get all pending album join requests for current owner",
)
def get_join_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    requests = (
        db.query(AlbumInvite, Album, User)
        .join(Album, Album.id == AlbumInvite.album_id)
        .join(User, User.id == AlbumInvite.requested_user_id)
        .filter(
            Album.owner_id == current_user.id,
            # AlbumInvite.status == "pending",
            AlbumInvite.is_active == True
        )
        .order_by(AlbumInvite.created_at.desc())
        .all()
    )

    data = []

    for invite, album, user in requests:

        data.append({
            "request_id": invite.id,
            "album_id": album.id,
            "album_name": album.album_name,

            "requested_user_id": user.id,
            "requested_user_name": user.username,
            "requested_user_mobile": user.mobile_number,

            "status": invite.status,

            "created_at": invite.created_at
        })

    return {
        "status": True,
        "message": "Join requests fetched successfully",
        "data": {
            "requests": data
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /album/{id}
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/album/{album_id}",
    response_model=ApiResponse[AlbumResponse],
    summary="Get a single album by ID",
)
def get_album(
    album_id: _uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    album = _get_album_or_404(album_id, current_user, db)

    photos = (
        db.query(Photo)
        .filter(Photo.album_id == album.id)
        .order_by(Photo.uploaded_at)
        .group_by(Photo.img_path)
        .all()
    )

    return {
        "status": True,
        "message": "Album fetched successfully",
        "data": {
            "id": album.id,
            "album_name": album.album_name,
            "event_date": album.event_date,
            "total_photos": album.total_photos,
            "total_size": album.total_size,
            "share_link": album.share_link,
            "is_active": album.is_active,
            "created_at": album.created_at,
            "photos": [
                PhotoResponse.model_validate(p) for p in photos
            ]
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /album/{album_id}/generate-share-link
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/album/generate-share-link",
    response_model=ApiResponse[ShareLinkResponse],
    summary="Generate (or regenerate) a unique share link for an album",
)
def generate_share_link(
    request: ShareLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album_id = request.album_id

    album = _get_album_or_404(album_id, current_user, db)

    if not album:
        return {
            "status": False,
            "message": "Album not found",
            "data": None
        }
    album.share_link = _uuid.uuid4().hex   # Regenerate token
    album.is_active  = True

    db.commit()
    db.refresh(album)
    return {
        "status": True,
        "message": "Share link generated successfully",
        "data": {
            "album_id": album.id,
            "share_link": album.share_link,
            "is_active": album.is_active
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /album/{album_id}/toggle-share
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/album/toggle-share",
    response_model=ApiResponse[ShareLinkResponse],
    summary="Toggle album sharing on/off",
)
def toggle_share(
    request: ShareLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album_id = request.album_id 
    album = _get_album_or_404(album_id, current_user, db)

    if not album:
        return {
            "status": False,
            "message": "Album not found",
            "data": None
        }

    album.is_active = not album.is_active
    db.commit()
    db.refresh(album)
    return {
        "status": True,
        "message": "Share link updated successfully",
        "data": {
            "album_id": album.id,
            "share_link": album.share_link,
            "is_active": album.is_active
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /album/share/{share_link}   ← PUBLIC (no auth)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/album/share/{share_link}",
    response_model=ApiResponse[PublicAlbumResponse],
   
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
        return {
            "status": False,
            "message": "Album not found",
            "data": None
        }

    photos = (
        db.query(Photo)
        .filter(Photo.album_id == album.id)
        .order_by(Photo.uploaded_at)
        .all()
    )

    return {
        "status": True,
        "message": "Album fetched successfully",
        "data": {
            "album_id": album.id,
            "album_name": album.album_name,
            "event_date": album.event_date,
            "total_photos": album.total_photos,
            "photos": [
                {
                    "id": p.id,
                    "img_path": p.img_path,
                    "person_id": str(p.person_id) if p.person_id else None
                }
                for p in photos
            ]
        }
     }


# ─────────────────────────────────────────────────────────────────────────────
# POST /album/join-request
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/album/join-request",
    response_model=ApiResponse[MessageResponse],
    summary="Request access to an album using album code",
)
def join_album_request(
    payload: JoinAlbumRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Find album
    album = (
        db.query(Album)
        .filter(
            Album.album_code == payload.album_code
        )
        .first()
    )

    if not album:
        return {
            "status": False,
            "message": "Invalid album code",
            "data": None
        }

    # Prevent owner requesting own album
    if album.owner_id == current_user.id:   
        return {
            "status": False,
            "message": "You are already the owner of this album",
            "data": None
        }

    # Check existing request
    existing_request = (
        db.query(AlbumInvite)
        .filter(
            AlbumInvite.album_id == album.id,
            AlbumInvite.requested_user_id == current_user.id
        )
        .first()
    )

    if existing_request:

        if existing_request.status == "approved":
            return {
                "status": False,
                "message": "You already have access to this album",
                "data": None
            }

        if existing_request.status == "pending":
            return {
                "status": False,
                "message": "Join request already pending",
                "data": None
            }

        if existing_request.status == "rejected":
            existing_request.status = "pending"
            existing_request.is_active = True

            db.commit()

            return {
                "status": True,
                "message": "Join request sent again successfully",
                "data": {
                    "message": "Waiting for album owner approval"
                }
            }

    # Create fresh request
    join_request = AlbumInvite(
        album_id=album.id,
        invited_by=album.owner_id,
        requested_user_id=current_user.id,

        invite_code=_uuid.uuid4().hex[:10],

        status="approved",
        is_active=True
    )

    db.add(join_request)
    db.commit()

    return {
        "status": True,
        "message": "Join request sent successfully",
        "data": {
            "message": "Waiting for album owner approval"
        }
    }
