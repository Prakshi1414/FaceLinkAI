# app/main.py
# ─────────────────────────────────────────────────────────────────────────────
# FaceLinkAI – FastAPI application entry point
#
# Run with:
#   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from app.ml.startup import bootstrap_faiss_from_db
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.database import engine
from app.db.init_db import init_db
from app.routers import albums, auth, gallery, photos, recognition


logging.basicConfig(
    level=logging.DEBUG if settings.APP_ENV == "development" else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan  (startup + shutdown)
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ───────────────────────────────────────────────────────────────
    logger.info("=== FaceLinkAI starting up ===")

    # Ensure storage directories exist
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("Temp directory  : %s", settings.TEMP_DIR)
    logger.info("Image directory : %s", settings.IMAGE_DIR)

    # Bootstrap FAISS index from existing DB embeddings
    # (This is non-blocking for startup; heavy model loading is lazy)
    try:
       bootstrap_faiss_from_db()
    except Exception as exc:
        logger.warning("FAISS bootstrap skipped (DB may be empty): %s", exc)

    logger.info("=== FaceLinkAI ready ===")
    yield

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("=== FaceLinkAI shutting down ===")
    engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FaceLinkAI – Studio Edition",
    version="1.0.0",
    contact={"name": "FaceLinkAI Engineering"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/")
def home():
    return {
        "message": "FaceLinkAI API is running successfully 🚀",
        "status": "active"
    }

# ─────────────────────────────────────────────────────────────────────────────
# CORS  (tighten allowed_origins in production)
# ─────────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "development" else [
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────────────────────────────────────────
# Static file serving for uploaded images
# ─────────────────────────────────────────────────────────────────────────────
_image_dir = Path(settings.IMAGE_DIR)
_image_dir.mkdir(parents=True, exist_ok=True)

# Ye rahi wo missing line:
app.mount("/images", StaticFiles(directory=str(_image_dir)), name="images")

logger.info("Serving static images from: %s", _image_dir.absolute())

# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(albums.router)
app.include_router(photos.router)
app.include_router(recognition.router)
app.include_router(gallery.router)

# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
def health():
    from app.ml.face_engine import faiss_index

    return {
        "status": "ok",
        "environment": settings.APP_ENV,
        "faiss_persons_indexed": faiss_index.total_persons,
    }

# ─────────────────────────────────────────────────────────────────────────────
# Allow `python app/main.py` for quick local testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=(settings.APP_ENV == "development"),
    )