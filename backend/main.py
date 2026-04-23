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
        # Step A: Temporary save
        temp_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step B: Image ka Hash sirf filename ke liye
        # Isse ye hoga ki 5 baar upload karne par folder mein 1 hi photo rahegi (Space bachegi)
        file_hash = face_engine.get_image_hash(temp_path)
        file_ext = os.path.splitext(file.filename)[1]
        permanent_path = os.path.join(IMAGE_DIR, f"{file_hash}{file_ext}")

        if not os.path.exists(permanent_path):
            shutil.move(temp_path, permanent_path)
        else:
            os.remove(temp_path)

        # Step C: Recognize faces
        matches = face_engine.recognize_faces(permanent_path, auto_save=False)
        
        for match in matches:
            final_name = name if name else match.get("person", f"user_{uuid.uuid4().hex[:6]}")
            
            # --- CHANGE HERE ---
            # Hum is_duplicate check nahi karenge. 
            # Har upload par add_embedding call hoga.
            add_embedding(final_name, match["embedding"], permanent_path)
            results.append({"registered_as": final_name, "status": "added"})

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