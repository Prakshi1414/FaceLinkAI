import os
import uuid
import shutil
from typing import List, Optional
 
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
 
from backend.database_helper import init_db
from backend.embedding_store import load_db
from backend.faiss_index import build_index
from backend import face_engine
 
# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="FaceLinkAI 🚀")
 
UPLOAD_DIR = "temp"
IMAGE_DIR  = "data/images"
DATA_DIR   = "data"
 
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR,  exist_ok=True)
os.makedirs(DATA_DIR,   exist_ok=True)
 
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
 
# Init DB on startup
init_db()
build_index()   # load existing embeddings into FAISS at startup
 
 
# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "FaceLinkAI Running 🚀"}
 
 
# ── Register (Bulk) ───────────────────────────────────────────────────────────
@app.post("/register-face")
async def register_face(
    files: List[UploadFile] = File(...),
    name:  Optional[str]    = Form(None),
):
    """
    FIX 1+2+3: Delegates entirely to register_bulk().
    - Saves temp files, calls register_bulk() with optional name.
    - register_bulk() handles dedup, auto-detect for unlabeled group images,
      and auto-merge after batch completion.
    """
    temp_paths = []
 
    for file in files:
        ext       = os.path.splitext(file.filename)[1].lower() or ".jpg"
        temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
        with open(temp_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        temp_paths.append(temp_path)
 
   
    results = face_engine.register_bulk(temp_paths, name=name if name else None)
 
    # Cleanup temp files
    for p in temp_paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
 
    return {"status": "complete", "processed": len(files), "details": results}
 
 
# ── Recognize ─────────────────────────────────────────────────────────────────
@app.post("/recognize-face")
async def recognize_face(file: UploadFile = File(...)):
    """
    Recognize all faces in the uploaded image.
    For group images, returns one entry per detected face.
    """
    ext       = os.path.splitext(file.filename)[1].lower() or ".jpg"
    temp_path = os.path.join(UPLOAD_DIR, f"recognize_{uuid.uuid4().hex}{ext}")
 
    with open(temp_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
 
    try:
        result = face_engine.recognize_faces(temp_path, auto_save=True)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
 
    return {"result": result}
 
 
# ── Gallery ───────────────────────────────────────────────────────────────────
@app.get("/get-gallery")
async def get_gallery():
    """
    Returns all DB entries grouped correctly.
    Deduplicates image paths per person before returning.
    """
    try:
        db_records = load_db()
 
        # Deduplicate: one entry per unique (name, image_path) pair
        seen    = set()
        gallery = []
        for r in db_records:
            key = (r["name"], r["image"])
            if key not in seen:
                seen.add(key)
                gallery.append({"name": r["name"], "image": r["image"]})
 
        return {"total": len(gallery), "gallery": gallery}
    except Exception as e:
        return {"error": str(e)}
 
 
# ── Merge duplicates (admin trigger) ─────────────────────────────────────────
@app.post("/merge-duplicates")
async def merge_duplicates():
    """
    FIX 4: Manual trigger for auto-merge.
    Useful after bulk uploads or if gallery shows duplicate persons.
    """
    try:
        face_engine.auto_merge_duplicates()
        return {"status": "merge complete"}
    except Exception as e:
        return {"error": str(e)}
 
 
# ── Stats ─────────────────────────────────────────────────────────────────────
@app.get("/stats")
async def stats():
    db_records = load_db()
    from collections import Counter
    name_counts = Counter(r["name"] for r in db_records)
    return {
        "total_embeddings": len(db_records),
        "total_persons":    len(name_counts),
        "persons":          dict(name_counts),
    }
 