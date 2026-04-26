

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime,
    Float, ForeignKey, Integer, LargeBinary, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# 1. register_user  (Studio / tenant account)
# ─────────────────────────────────────────────────────────────────────────────
class RegisterUser(Base):
    __tablename__ = "register_user"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    studio_name    = Column(Text, nullable=False)
    mobile_number  = Column(Text, nullable=False, unique=True)
    email          = Column(Text, nullable=True,  unique=True)
    password_hash  = Column(Text, nullable=False)
    created_at     = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    albums = relationship(
        "Album",
        back_populates="studio",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<RegisterUser id={self.id} studio={self.studio_name!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# 2. albums
# ─────────────────────────────────────────────────────────────────────────────
class Album(Base):
    __tablename__ = "albums"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    register_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("register_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    album_name   = Column(Text, nullable=False)
    event_name   = Column(Text, nullable=True)
    event_date   = Column(Date, nullable=True)
    total_photos = Column(Integer, default=0, nullable=False)
    total_size   = Column(BigInteger, default=0, nullable=False)   # bytes
    share_link   = Column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    is_active    = Column(Boolean, default=True, nullable=False)
    created_at   = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    studio = relationship("RegisterUser", back_populates="albums")
    photos = relationship(
        "Photo",
        back_populates="album",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Album id={self.id} name={self.album_name!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# 3. photos
# ─────────────────────────────────────────────────────────────────────────────
class Photo(Base):
    __tablename__ = "photos"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    album_id = Column(
        UUID(as_uuid=True),
        ForeignKey("albums.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    img_path    = Column(Text, nullable=False)
    # person_id: UUID assigned by the FAISS clustering engine (global across tenants' albums)
    person_id   = Column(String(36), nullable=True, index=True)
    # embedding stored as raw bytes (numpy float32 array, 512-dim for Facenet512)
    embedding   = Column(LargeBinary, nullable=True)
    file_size   = Column(BigInteger, default=0, nullable=False)    # bytes
    uploaded_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    album = relationship("Album", back_populates="photos")

    def __repr__(self) -> str:
        return f"<Photo id={self.id} person_id={self.person_id!r}>"