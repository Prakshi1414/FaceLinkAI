from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
import cv2
import uuid
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
async def register_face(file: UploadFile = File(...), name: str = Form(...)):
    file_path = f"{IMAGE_DIR}/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Faces extract karo
    faces = face_engine.extract_faces(file_path)
    
    for i, face in enumerate(faces):
        face_img = (face["face"] * 255).astype("uint8")
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        temp_crop = f"temp/reg_face_{i}.jpg"
        cv2.imwrite(temp_crop, face_img)
        
        # --- SMART CHECK START ---
        actual_name = name # Default name jo aapne likha hai
        
        try:
            # Check karo agar DB khali nahi hai toh hi search karo
            emb = face_engine.get_embedding(temp_crop)
            results = face_engine.search_face(emb)
            
            # Agar results mile (DB khali nahi hai)
            if results:
                filtered = [r for r in results if r["score"] > 0.8]
                if filtered:
                    actual_name = filtered[0]["name"]
                elif i > 0:
                    # Agar group mein dusra banda unknown hai
                    actual_name = f"user_{uuid.uuid4().hex[:6]}"
        except:
            # Agar DB khali hai toh search_face error dega, hum yahan handle kar lenge
            # Pehla user hamesha wahi banega jo aapne 'name' field mein likha hai
            actual_name = name
        # --- SMART CHECK END ---

        add_embedding(actual_name, file_path, custom_path=temp_crop)

    build_index() 
  
    return {"message": f"{name} faces registered successfully."}

# ---------------- RECOGNIZE FACE ----------------
@app.post("/recognize-face")
async def recognize_face(file: UploadFile = File(...)):
    temp_path = f"{UPLOAD_DIR}/test.jpg"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = face_engine.recognize_faces(temp_path)
    # 🔥 AUTO-CLEAN LOGIC: temp folder ki saari files uda do
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