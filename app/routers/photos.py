
from __future__ import annotations

import logging
import shutil
import uuid as _uuid
from pathlib import Path
from typing import List, Optional, Tuple

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

_ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
)


# ─────────────────────────────────────────────────────────────────────────────
# Directory helpers (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def _temp_dir(studio_id: str, album_id: str) -> Path:
    d = Path(settings.TEMP_DIR) / studio_id / album_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _image_dir(studio_id: str, album_id: str) -> Path:
    d = Path(settings.IMAGE_DIR) / studio_id / album_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_delete(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        logger.warning("Could not delete temp file %s: %s", path, exc)


# ─────────────────────────────────────────────────────────────────────────────
# TempFileHandler (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class TempFileHandler:
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
        self._temp_path.write_bytes(file_bytes)
        logger.debug("Temp write: %s (%d bytes)", self._temp_path, len(file_bytes))

    def __enter__(self) -> "TempFileHandler":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._committed:
            _safe_delete(self._temp_path)
            if exc_type is not None:
                logger.debug(
                    "Temp file deleted after failure: %s | reason: %s",
                    self._temp_path, exc_val,
                )
        return False

    @property
    def path(self) -> Path:
        return self._temp_path

    @property
    def safe_name(self) -> str:
        return self._safe_name

    def commit(self, image_dir: Path) -> Path:
        final_path = image_dir / self._safe_name
        shutil.move(str(self._temp_path), str(final_path))
        self._committed = True
        logger.debug("Committed: %s → %s", self._temp_path, final_path)
        return final_path


# ─────────────────────────────────────────────────────────────────────────────
# Image validation (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def _validate_image(path: Path) -> None:
    try:
        with Image.open(path) as img:
            img.verify()
    except UnidentifiedImageError as exc:
        raise ValueError(f"Not a recognisable image file: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Image validation failed: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# FIX: AI pipeline returns list of face results (multi-face support)
# ─────────────────────────────────────────────────────────────────────────────

def _run_ai_pipeline(
    temp_path: Path,
    user_id: str,      # FIX 4: required for per-user FAISS index
    threshold: float,
) -> Tuple[List[Tuple[Optional[str], Optional[bytes]]], str, Optional[str]]:
    """
    Run detection → embedding → FAISS on the image at temp_path.

    Returns
    -------
    (face_list, overall_status, message)

    face_list : List of (person_id_or_None, embedding_bytes_or_None)
                One entry per detected face.
                Empty list means no face was detected.

    overall_status : "ok"      – at least one face found and processed
                     "no_face" – image is valid but no face detected
    """
    # FIX 1+4: pass user_id, get back a list of face results
    face_results = process_image_for_clustering(
        image_path=str(temp_path),
        user_id=user_id,
        threshold=threshold,
    )

    if not face_results:
        return [], "no_face", "No face detected in image"

    face_list = [
        (person_id, embedding_to_bytes(embedding) if embedding is not None else None)
        for person_id, embedding, _is_new in face_results
    ]
    return face_list, "ok", None


# ─────────────────────────────────────────────────────────────────────────────
# POST /photos/upload/{album_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/upload-album-photos",
    response_model=UploadPhotosResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload photos to an album. Face detection runs automatically per photo.",
)
async def upload_album_photos(
    album_id: _uuid.UUID = Form(..., description="Target album UUID"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadPhotosResponse:

    # ── Guard: album must belong to this studio ───────────────────────────────
    album: Optional[Album] = (
        db.query(Album)
        .filter(
            Album.id == album_id,
            Album.user_id == current_user.id,
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
    img_dir    = _image_dir(studio_id, album_id_s)

    results:      List[UploadResult] = []
    photos_added: int = 0
    bytes_added:  int = 0

    # ── Per-file loop ─────────────────────────────────────────────────────────
    for upload_file in files:
        original_name = upload_file.filename or "unknown"
        ext           = Path(original_name).suffix.lower()

        # ── Extension guard ───────────────────────────────────────────────────
        if ext not in _ALLOWED_EXTENSIONS:
            results.append(UploadResult(
                filename=original_name,
                status="error",
                message=f"Unsupported file type '{ext}'. "
                        f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
            ))
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
            continue

        file_size = len(file_bytes)
        if file_size == 0:
            results.append(UploadResult(
                filename=original_name,
                status="error",
                message="Received an empty file (0 bytes).",
            ))
            continue

        # ── Two-phase handling ────────────────────────────────────────────────
        try:
            with TempFileHandler(file_bytes, original_name, studio_id, album_id_s) as tmp:

                # Phase 1 – validate image
                try:
                    _validate_image(tmp.path)
                except ValueError as exc:
                    results.append(UploadResult(
                        filename=original_name,
                        status="error",
                        message=str(exc),
                    ))
                    continue

                # Phase 2 – AI pipeline
                try:
                    face_list, photo_status, ai_msg = _run_ai_pipeline(
                        temp_path=tmp.path,
                        user_id=studio_id,       # FIX 4
                        threshold=settings.FACE_SIMILARITY_THRESHOLD,
                    )
                except Exception as exc:
                    results.append(UploadResult(
                        filename=original_name,
                        status="error",
                        message=f"AI processing error: {exc}",
                    ))
                    logger.exception("AI pipeline failed for %s", original_name)
                    continue

                # ── Commit file to permanent storage ──────────────────────────
                final_path  = tmp.commit(img_dir)
                relative_db = str(Path(studio_id) / album_id_s / tmp.safe_name)

                if photo_status == "no_face" or not face_list:
                    # ── No face: save photo row without person/embedding ───────
                    # FIX 2: no user_id field on Photo model
                    photo = Photo(
                        album_id  = album_id,
                        img_path  = relative_db,
                        person_id = None,
                        embedding = None,
                        file_size = file_size,
                    )
                    db.add(photo)
                    photos_added += 1
                    bytes_added  += file_size

                    results.append(UploadResult(
                        filename  = original_name,
                        status    = "no_face",
                        person_id = None,
                        message   = ai_msg,
                    ))
                    logger.info(
                        "No face – photo saved without embedding: %s", relative_db
                    )

                else:
                    # ── One or more faces: save one Photo row per face ─────────
                    # For the UploadResult we report the first face's person_id
                    # (most common case is one face per photo).
                    first_result_appended = False

                    for person_id, embedding_bytes in face_list:
                        # FIX 2: no user_id field on Photo model
                        photo = Photo(
                            album_id  = album_id,
                            img_path  = relative_db,
                            person_id = person_id,
                            embedding = embedding_bytes,
                            file_size = file_size,
                        )
                        db.add(photo)
                        photos_added += 1
                        bytes_added  += file_size

                        if not first_result_appended:
                            results.append(UploadResult(
                                filename  = original_name,
                                status    = "ok",
                                person_id = person_id,
                                message   = (
                                    f"{len(face_list)} face(s) detected"
                                    if len(face_list) > 1 else None
                                ),
                            ))
                            first_result_appended = True

                    logger.info(
                        "Processed %s → %d face(s) → person_ids=%s  final=%s",
                        original_name,
                        len(face_list),
                        [pid for pid, _ in face_list],
                        final_path,
                    )

        except Exception as exc:
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
        album_id       = album_id,
        total_uploaded = photos_added,
        results        = results,
    )