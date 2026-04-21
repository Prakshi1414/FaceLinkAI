from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
from backend import face_engine
from backend.embedding_store import add_embedding
from backend.faiss_index import build_index
from backend.clustering_engine import run_clustering

app = FastAPI(title="FaceLinkAI 🚀")

UPLOAD_DIR = "temp"
KNOWN_DIR = "data/images"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KNOWN_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "FaceLinkAI Running 🚀"}

IMAGE_DIR = "data/images"

# ---------------- REGISTER FACE ----------------
@app.post("/register-face")
async def register_face(file: UploadFile = File(...), name: str = Form(...)):
    file_path = f"{IMAGE_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    add_embedding(name, file_path)
    build_index() 
    return {"message": f"{name} added successfully"}

# ---------------- RECOGNIZE FACE ----------------
@app.post("/recognize-face")
async def recognize_face(file: UploadFile = File(...)):
    temp_path = f"{UPLOAD_DIR}/test.jpg"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = face_engine.recognize_faces(temp_path)

    return {"result": result}

# ---------------- CLUSTERING ----------------
@app.get("/run-clustering")
def cluster_faces():
    result = run_clustering()
    return {"clusters": result}