# app/schemas/schemas.py
# ─────────────────────────────────────────────────────────────────────────────
# All Pydantic v2 schemas used in request bodies and response models.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ═════════════════════════════════════════════════════════════════════════════
# AUTH
# ═════════════════════════════════════════════════════════════════════════════

class RegisterUserRequest(BaseModel):
    studio_name:   str          = Field(..., min_length=2, max_length=120)
    mobile_number: str          = Field(..., min_length=7, max_length=20)
    email:         Optional[EmailStr] = None
    password:      str          = Field(..., min_length=6)


class RegisterUserResponse(BaseModel):
    id:            uuid.UUID
    studio_name:   str
    mobile_number: str
    email:         Optional[str]
    created_at:    datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    mobile_number: str
    password:      str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    studio_name:  str
    user_id:      uuid.UUID


# ═════════════════════════════════════════════════════════════════════════════
# ALBUM
# ═════════════════════════════════════════════════════════════════════════════

class CreateAlbumRequest(BaseModel):
    album_name:  str            = Field(..., min_length=1, max_length=200)
    event_name:  Optional[str]  = None
    event_date:  Optional[date] = None


class AlbumResponse(BaseModel):
    id:               uuid.UUID
    album_name:       str
    event_name:       Optional[str]
    event_date:       Optional[date]
    total_photos:     int
    total_size:       int
    share_link:       str
    is_active:        bool
    created_at:       datetime

    model_config = {"from_attributes": True}


class ShareLinkResponse(BaseModel):
    album_id:   uuid.UUID
    share_link: str
    is_active:  bool


# ═════════════════════════════════════════════════════════════════════════════
# PHOTO
# ═════════════════════════════════════════════════════════════════════════════

class PhotoResponse(BaseModel):
    id:          uuid.UUID
    album_id:    uuid.UUID
    img_path:    str
    person_id:   Optional[str]
    file_size:   int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PublicPhotoItem(BaseModel):
    id:        uuid.UUID
    img_path:  str
    person_id: Optional[str]

    model_config = {"from_attributes": True}


class PublicAlbumResponse(BaseModel):
    album_id:     uuid.UUID
    album_name:   str
    event_name:   Optional[str]
    event_date:   Optional[date]
    total_photos: int
    photos:       List[PublicPhotoItem]


class UploadResult(BaseModel):
    filename:   str
    status:     str          # "ok" | "no_face" | "error"
    person_id:  Optional[str] = None
    message:    Optional[str] = None


class UploadPhotosResponse(BaseModel):
    album_id:       uuid.UUID
    total_uploaded: int
    results:        List[UploadResult]


# ═════════════════════════════════════════════════════════════════════════════
# RECOGNITION
# ═════════════════════════════════════════════════════════════════════════════

class RecognizedPhoto(BaseModel):
    photo_id:    uuid.UUID
    img_path:    str
    album_id:    uuid.UUID
    album_name:  str
    similarity:  float


class RecognizeResponse(BaseModel):
    person_id:        Optional[str]
    is_new_person:    bool
    similarity_score: Optional[float]
    matched_photos:   List[RecognizedPhoto]


# ═════════════════════════════════════════════════════════════════════════════
# GALLERY
# ═════════════════════════════════════════════════════════════════════════════

class PersonGroup(BaseModel):
    person_id:    str
    total_photos: int
    photos:       List[PhotoResponse]


class AlbumGallery(BaseModel):
    album_id:    uuid.UUID
    album_name:  str
    event_name:  Optional[str]
    persons:     List[PersonGroup]


class GalleryResponse(BaseModel):
    studio_id: uuid.UUID
    albums:    List[AlbumGallery]


# ═════════════════════════════════════════════════════════════════════════════
# GENERIC
# ═════════════════════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    message: str