from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
import cv2
import uuid
from typing import List, Optional
from .database_helper import init_db # Database initialization
from fastapi.staticfiles import StaticFiles
from backend import face_engine
from backend.embedding_store import add_embedding
from backend.faiss_index import build_index
from backend.clustering_engine import run_clustering



app = FastAPI(title="FaceLinkAI 🚀")

UPLOAD_DIR = "temp"

app.mount("/data", StaticFiles(directory="data"), name="data")
KNOWN_DIR = "data/images"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KNOWN_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "FaceLinkAI Running 🚀"}

IMAGE_DIR = "data/images"

# ---------------- REGISTER FACE ----------------
@app.post("/register-face")
async def register_face(
    files: List[UploadFile] = File(...), 
    name: Optional[str] = Form(None)
):
    results = []
    new_embeddings_added = False
    
    for file in files:
        unique_id = uuid.uuid4().hex[:8]
        file_ext = os.path.splitext(file.filename)[1]
        file_path = os.path.join(IMAGE_DIR, f"reg_{unique_id}{file_ext}")

        # 1. File Save
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Face extraction
        faces = face_engine.extract_faces(file_path)
        if not faces:
            results.append({"file": file.filename, "status": "No face detected"})
            continue

        face = faces[0]
        face_img = (face["face"] * 255).astype("uint8")
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        
        temp_crop = f"temp/reg_{unique_id}.jpg"
        cv2.imwrite(temp_crop, face_img)
        
        # 3. Embedding
        emb = face_engine.get_embedding(temp_crop)
        if emb is not None:
            final_name = name if name else f"user_{uuid.uuid4().hex[:6]}"
            add_embedding(final_name, emb, file_path)
            new_embeddings_added = True
            results.append({"file": file.filename, "registered_as": final_name})
        
        # Temp file clean karein taaki memory full na ho
        if os.path.exists(temp_crop):
            os.remove(temp_crop)

    # 🔥 CRITICAL: Sab khatam hone ke baad sirf EK baar index banayein
    if new_embeddings_added:
        face_engine.build_index() 
    
    return {"total_uploaded": len(files), "details": results}

# ---------------- RECOGNIZE FACE ----------------
@app.post("/recognize-face")
async def recognize_face(file: UploadFile = File(...)):
    temp_path = f"{UPLOAD_DIR}/test.jpg"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = face_engine.recognize_faces(temp_path)
    #  AUTO-CLEAN LOGIC: temp folder
    ''' for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")'''
    return {"result": result}
    

# ---------------- CLUSTERING ----------------
@app.get("/run-clustering")
def cluster_faces():
    result = run_clustering()
    return {"clusters": result}

init_db()