# app/schemas/schemas.py
# ─────────────────────────────────────────────────────────────────────────────
# All Pydantic v2 schemas used in request bodies and response models.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
from pydantic import field_validator
import re
import uuid
from datetime import date, datetime
from typing import Any, Optional
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.models import User

# ═════════════════════════════════════════════════════════════════════════════
# AUTH
# ═════════════════════════════════════════════════════════════════════════════


class RegisterUserRequest(BaseModel):
    studio_name:   str = Field(..., min_length=2, max_length=120)
    mobile_number: str = Field(..., min_length=7, max_length=20)
    email:         Optional[EmailStr] = None
    password:      str = Field(..., min_length=6)
    username: str

    @field_validator("mobile_number")
    def validate_phone(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone must be exactly 10 digits (0-9 only)")
        return v

    @field_validator("email")
    def validate_email(cls, v):
        if v is None:
            return v

        pattern = r"^[\w\.-]+@[\w\.-]+\.com$"
        if not re.match(pattern, v):
            raise ValueError("Email must contain @ and .com")

        return v

    @field_validator("password")
    def validate_password(cls, v):

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if v.isdigit() or v.isalpha():
            raise ValueError("Password must include letters and numbers")

        weak = ["123456", "abcdef", "password", "111111", "000000"]
        if any(x in v.lower() for x in weak):
            raise ValueError("Password is too weak or sequential")

        return v


class RegisterUserResponse(BaseModel):
    id:            uuid.UUID
    studio_name:   str
    mobile_number: str
    email:         Optional[str]
    created_at:    datetime
    username: Optional[str]
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    mobile_number: str
    password:      str

    @field_validator("mobile_number")
    def validate_phone(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    studio_name:  str
    user_id:      uuid.UUID
    username: str

# ═════════════════════════════════════════════════════════════════════════════
# ALBUM
# ═════════════════════════════════════════════════════════════════════════════


class CreateAlbumRequest(BaseModel):
    album_name:  str = Field(..., min_length=1, max_length=200)
    event_date:  Optional[date] = None


class AlbumResponse(BaseModel):
    id: uuid.UUID
    album_name: str
    event_date: Optional[date]
    total_photos: int
    total_size: int
    share_link: Optional[str]
    is_active: bool
    created_at: datetime
    photos: List[PhotoResponse]
    model_config = {"from_attributes": True}


class ShareLinkRequest(BaseModel):
    album_id: uuid.UUID


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
    person_id: Optional[uuid.UUID]
    file_size:   int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PublicPhotoItem(BaseModel):
    id:        uuid.UUID
    img_path:  str
    person_id: Optional[str]

    model_config = {"from_attributes": True}


class PublicAlbumResponse(BaseModel):
    album_id: uuid.UUID
    album_name: str
    event_date: Optional[date]
    total_photos: int
    photos: List[PublicPhotoItem]


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
    persons:     List[PersonGroup]


class GalleryResponse(BaseModel):
    user_id: uuid.UUID
    albums:    List[AlbumGallery]


# ═════════════════════════════════════════════════════════════════════════════
# GENERIC
# ═════════════════════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    message: str
