

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
# ─────────────────────────────────────────────────────────────────────────────
# 1. register_user  (Studio / tenant account)
# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    studio_name    = Column(Text, nullable=True)
    mobile_number  = Column(Text, nullable=False, unique=True)
    email          = Column(Text, nullable=True,  unique=True)
    password_hash  = Column(Text, nullable=False)
    created_at     = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    username = Column(String, nullable=True)
    role = Column(String, default="studio")

    # ── Relationships ─────────────────────────────────────────────────────────
    
    # albums created by studio
    created_albums = relationship(
        "Album",
        foreign_keys="Album.user_id",
        back_populates="studio",
        cascade="all, delete-orphan",
    )

    # albums assigned to this user as client
    client_albums = relationship(
        "Album",
        foreign_keys="Album.owner_id",
        back_populates="client",
    )

    def __repr__(self) -> str:
        return f"<user id={self.id} studio={self.studio_name!r}>"

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
    user_id = Column(
    UUID(as_uuid=True),
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
    )

    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    album_code = Column(
        String,
        unique=True,
        nullable=False
    )
    
    album_name   = Column(Text, nullable=False)
    event_date   = Column(Date, nullable=True)
    total_photos = Column(Integer, default=0, nullable=False)
    total_size   = Column(BigInteger, default=0, nullable=False)   # bytes
    share_link = Column(String(64), unique=True, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at   = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
      # Studio relationship (creator)
    studio = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="created_albums"
    )

    # Client relationship (owner/handler)
    client = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="client_albums"
    )


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
class Person(Base):
    __tablename__ = "persons"

    person_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    name = Column(Text, nullable=True)
    centroid = Column(ARRAY(Float), nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    album_id = Column(UUID(as_uuid=True), ForeignKey("albums.id"))

    created_at = Column(DateTime(timezone=True), default=_utcnow)    

class AlbumInvite(Base):
    __tablename__ = "album_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    album_id = Column(UUID(as_uuid=True), ForeignKey("albums.id"))
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    requested_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    invite_code = Column(String(20), unique=True)

    status = Column(String(20), default="Approved")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)