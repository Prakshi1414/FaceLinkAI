from importlib.resources import files
from fastapi import FastAPI, Form
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form
import os, uuid, shutil, cv2
from .database_helper import init_db # Database initialization
from fastapi.staticfiles import StaticFiles
from backend import face_engine
from backend.embedding_store import load_db, update_name_in_db
from backend.embedding_store import add_embedding
from backend.clustering_engine import perform_clustering, auto_merge_clusters
from backend.faiss_index import build_index



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

# main.py mein register_face ko aise fix karein
@app.post("/register-face")
async def register_face(files: List[UploadFile] = File(...), name: Optional[str] = Form(None)):
    results = []
    for file in files:
        # 1. Permanent save karein (reg_... naam se)
        unique_id = uuid.uuid4().hex[:8]
        file_path = os.path.join(IMAGE_DIR, f"reg_{unique_id}.jpg")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Sirf recognize karein (auto_save=False taaki hash logic auto-save na kare)
        matches = face_engine.recognize_faces(file_path, auto_save=False)
        
        for match in matches:
            final_name = name if name else f"user_{uuid.uuid4().hex[:6]}"
            # 3. Yahan manually 1 baar add karein
            add_embedding(final_name, match["embedding"], file_path)
            results.append({"registered_as": final_name})

    build_index()
    return {"status": "complete", "details": results}
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
async def run_clustering():
    try:
        # 1. Clustering run karein (Groups dhundhein)
        clusters = perform_clustering()
        
        if isinstance(clusters, str):
            return {"message": clusters}

        # 2. Database mein auto-merge karein (Names update karein)
        merge_summary = auto_merge_clusters(clusters)

        # 3. 🔥 CRITICAL: Index ko rebuild karein taaki nayi pehchan active ho jaye
        if merge_summary["updated"] > 0:
            build_index()

        return {
            "status": "Clustering and Merging Complete",
            "total_clusters": len(clusters),
            "records_updated": merge_summary["updated"],
            "groups_merged": merge_summary["merged_groups"]
        }
        
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get-gallery")
async def get_gallery():
    try:
        db_records = load_db()
        gallery_data = [{"name": r["name"], "image": r["image"]} for r in db_records]
        return {"total": len(gallery_data), "gallery": gallery_data}
    except Exception as e:
        return {"error": str(e)}

init_db()