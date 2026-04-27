# app/routers/photos.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /upload-album-photos
#
# Two-phase file handling per image:
#
#   Phase 1 – TEMP
#     • Write raw bytes to  TEMP_DIR/<studio_id>/<album_id>/<uuid>.<ext>
#     • Validate the file can be opened as an image (PIL check)
#
#   Phase 2 – PROCESS
#     • Run RetinaFace detection on the temp file
#     • Run DeepFace Facenet512 embedding on the temp file
#     • FAISS cosine search → assign / create person_id
#
#   On SUCCESS (face found OR no-face-but-valid-image)
#     • shutil.move() temp file → IMAGE_DIR/<studio_id>/<album_id>/
#     • Persist Photo row in PostgreSQL
#     • Update album.total_photos + album.total_size
#
#   On ANY FAILURE (bad file, corrupt image, unhandled exception)
#     • Delete temp file immediately
#     • Append error result – do NOT write a DB row
#     • Continue to next file (never abort the whole batch)
#
# Directory layout
#   data/
#     temp/    ← landing zone  (never referenced by DB)
#     images/  ← permanent store  (img_path in DB is relative to here)
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
import shutil
import uuid as _uuid
from pathlib import Path
from typing import  List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.ml.face_engine import embedding_to_bytes, process_image_for_clustering
from app.models.models import Album, Photo, User
from app.schemas.schemas import UploadPhotosResponse, UploadResult
from app.utils.auth import get_current_user

router = APIRouter(tags=["Photos"])
logger = logging.getLogger(__name__)

# Permitted image extensions (lower-case)
_ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
)


# ─────────────────────────────────────────────────────────────────────────────
# Directory helpers
# ─────────────────────────────────────────────────────────────────────────────

def _temp_dir(studio_id: str, album_id: str) -> Path:
    """Return (and create) the temp subdirectory for this studio/album."""
    d = Path(settings.TEMP_DIR) / studio_id / album_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _image_dir(studio_id: str, album_id: str) -> Path:
    """Return (and create) the permanent image subdirectory for this studio/album."""
    d = Path(settings.IMAGE_DIR) / studio_id / album_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_delete(path: Path) -> None:
    """Delete a file, swallowing any OS-level errors (already gone, race, etc.)."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not delete temp file %s: %s", path, exc)


# ─────────────────────────────────────────────────────────────────────────────
# TempFileHandler – context manager
#
# Usage:
#   with TempFileHandler(file_bytes, original_filename, studio_id, album_id) as tmp:
#       # tmp.path is the absolute Path to the temp file
#       do_processing(tmp.path)
#       tmp.commit(image_dir)   # moves file to permanent location
#   # If an exception escapes the block, temp file is deleted automatically.
# ─────────────────────────────────────────────────────────────────────────────

class TempFileHandler:
    """
    Writes uploaded bytes to TEMP_DIR and tracks whether they have been
    committed (moved) to IMAGE_DIR.  Cleans up on any failure.
    """

    def __init__(
        self,
        file_bytes: bytes,
        original_filename: str,
        studio_id: str,
        album_id: str,
    ) -> None:
        ext = Path(original_filename).suffix.lower()
        safe_stem = _uuid.uuid4().hex
        self._safe_name = f"{safe_stem}{ext}"
        self._temp_path = _temp_dir(studio_id, album_id) / self._safe_name
        self._committed = False

        # Write bytes to temp location immediately
        self._temp_path.write_bytes(file_bytes)
        logger.debug("Temp write: %s (%d bytes)", self._temp_path, len(file_bytes))

    # ── Context manager protocol ──────────────────────────────────────────────
    def __enter__(self) -> "TempFileHandler":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._committed:
            # Something went wrong (or commit() was never called) → clean up
            _safe_delete(self._temp_path)
            if exc_type is not None:
                logger.debug(
                    "Temp file deleted after failure: %s | reason: %s",
                    self._temp_path, exc_val,
                )
        return False  # never suppress exceptions

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def path(self) -> Path:
        """Absolute path to the temp file."""
        return self._temp_path

    @property
    def safe_name(self) -> str:
        """UUID-based filename (e.g. 'a3f1…jpg')."""
        return self._safe_name

    # ── Commit ────────────────────────────────────────────────────────────────
    def commit(self, image_dir: Path) -> Path:
        """
        Move the temp file to *image_dir*.
        Must be called inside the ``with`` block after successful processing.
        Returns the final absolute path.
        """
        final_path = image_dir / self._safe_name
        shutil.move(str(self._temp_path), str(final_path))
        self._committed = True
        logger.debug("Committed: %s → %s", self._temp_path, final_path)
        return final_path


# ─────────────────────────────────────────────────────────────────────────────
# Image validation
# ─────────────────────────────────────────────────────────────────────────────

def _validate_image(path: Path) -> None:
    """
    Raise ValueError if the file at *path* cannot be opened as a valid image.
    This catches corrupted uploads, zero-byte files, and wrong-extension tricks
    before the heavy AI models even touch the data.
    """
    try:
        with Image.open(path) as img:
            img.verify()   # checks headers without decoding every pixel
    except UnidentifiedImageError as exc:
        raise ValueError(f"Not a recognisable image file: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Image validation failed: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Single-file processing pipeline
#
# Returns (person_id | None, embedding_bytes | None, photo_status, message)
# Raises on hard errors that should mark the file as "error" in results.
# ─────────────────────────────────────────────────────────────────────────────

def _run_ai_pipeline(
    temp_path: Path,
    threshold: float,
) -> Tuple[Optional[str], Optional[bytes], str, Optional[str]]:
    """
    Run detection → embedding → FAISS on the image at *temp_path*.

    Returns
    -------
    (person_id, embedding_bytes, status_str, message_str)
      status_str  : "ok" | "no_face"
      message_str : human-readable note (None when status is "ok")
    """
    person_id, embedding, _is_new = process_image_for_clustering(
        image_path=str(temp_path),
        threshold=threshold,
    )

    if person_id is None:
     return None, None, "no_face", "No face detected in image"

    return (
        person_id,
        embedding_to_bytes(embedding),
        "ok",
        None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /upload-album-photos
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/upload-album-photos",
    response_model=UploadPhotosResponse,
    status_code=status.HTTP_201_CREATED,
    summary=(
        "Upload photos to an album. "
        "Files land in TEMP_DIR first; "
        "on success they move to IMAGE_DIR; "
        "on any failure the temp file is deleted."
    ),
)
async def upload_album_photos(
    album_id: _uuid.UUID = Form(..., description="Target album UUID"),
    files: List[UploadFile] = File(..., description="One or more image files"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadPhotosResponse:

    # ── Guard: album must belong to this studio ───────────────────────────────
    album: Optional[Album] = (
        db.query(Album)
        .filter(
            Album.id == album_id,
            Album.user_id == current_user.id
        )
        .first()
    )
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found.",
        )

    studio_id  = str(current_user.id)
    album_id_s = str(album_id)
    img_dir    = _image_dir(studio_id, album_id_s)   # created if absent

    results:      List[UploadResult] = []
    photos_added: int = 0
    bytes_added:  int = 0

    # ── Per-file loop ─────────────────────────────────────────────────────────
    for upload_file in files:
        original_name = upload_file.filename or "unknown"
        ext           = Path(original_name).suffix.lower()

        # ── Extension guard (before reading bytes) ────────────────────────────
        if ext not in _ALLOWED_EXTENSIONS:
            results.append(UploadResult(
                filename=original_name,
                status="error",
                message=f"Unsupported file type '{ext}'. "
                        f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
            ))
            logger.warning("Rejected unsupported extension: %s", original_name)
            continue

        # ── Read raw bytes ────────────────────────────────────────────────────
        try:
            file_bytes = await upload_file.read()
        except Exception as exc:
            results.append(UploadResult(
                filename=original_name,
                status="error",
                message=f"Could not read upload stream: {exc}",
            ))
            logger.error("Stream read failed for %s: %s", original_name, exc)
            continue

        file_size = len(file_bytes)

        if file_size == 0:
            results.append(UploadResult(
                filename=original_name,
                status="error",
                message="Received an empty file (0 bytes).",
            ))
            continue

        # ── Two-phase handling inside TempFileHandler context ─────────────────
        try:
            with TempFileHandler(file_bytes, original_name, studio_id, album_id_s) as tmp:

                # Phase 1 – validate image integrity
                try:
                    _validate_image(tmp.path)
                except ValueError as exc:
                    # __exit__ will delete temp file because commit() not called
                    results.append(UploadResult(
                        filename=original_name,
                        status="error",
                        message=str(exc),
                    ))
                    logger.warning("Image validation failed %s: %s", original_name, exc)
                    continue   # skip to next file; __exit__ cleans up

                # Phase 2 – run AI pipeline
                try:
                    person_id, embedding_bytes, photo_status, ai_msg = _run_ai_pipeline(
                        temp_path=tmp.path,
                        threshold=settings.FACE_SIMILARITY_THRESHOLD,
                    )
                except Exception as exc:
                    results.append(UploadResult(
                        filename=original_name,
                        status="error",
                        message=f"AI processing error: {exc}",
                    ))
                    logger.exception("AI pipeline failed for %s", original_name)
                    continue   # __exit__ cleans up temp file

                # ── SUCCESS: move temp → permanent ────────────────────────────
                final_path  = tmp.commit(img_dir)
                # Relative path stored in DB (relative to IMAGE_DIR root)
                relative_db = str(Path(studio_id) / album_id_s / tmp.safe_name)

                # ── Persist Photo row ─────────────────────────────────────────
                if embedding_bytes is not None:
                    photo = Photo(
                        album_id=album_id,
                        user_id=current_user.id,
                        img_path=relative_db,
                        person_id=person_id,
                        embedding=embedding_bytes,
                        file_size=file_size,
                    )
                else:
                    photo = Photo(
                        album_id=album_id,
                        user_id=current_user.id,
                        img_path=relative_db,
                        person_id=None,
                        embedding=None,
                        file_size=file_size,
                    )
                db.add(photo)

                photos_added += 1
                bytes_added  += file_size

                results.append(UploadResult(
                    filename=original_name,
                    status=photo_status,
                    person_id=person_id,
                    message=ai_msg,
                ))

                logger.info(
                    "Processed %s → person_id=%s  status=%s  final=%s",
                    original_name, person_id, photo_status, final_path,
                )

        except Exception as exc:
            # Outer safety net: TempFileHandler.__exit__ already cleaned up.
            results.append(UploadResult(
                filename=original_name,
                status="error",
                message=f"Unexpected error: {exc}",
            ))
            logger.exception("Unhandled error for file %s", original_name)

    # ── Flush DB writes and update album counters ─────────────────────────────
    if photos_added > 0:
        album.total_photos += photos_added
        album.total_size   += bytes_added
        db.commit()
        logger.info(
            "Album %s updated: +%d photos, +%d bytes.",
            album_id, photos_added, bytes_added,
        )

    return UploadPhotosResponse(
        album_id=album_id,
        total_uploaded=photos_added,
        results=results,
    )