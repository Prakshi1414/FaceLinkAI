from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
from backend import face_engine

app = FastAPI(title="FaceLinkAI 🚀")

UPLOAD_DIR = "temp"
KNOWN_DIR = "data/known_faces"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KNOWN_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "FaceLinkAI Running 🚀"}


# ---------------- REGISTER FACE ----------------
@app.post("/register-face")
async def register_face(
    file: UploadFile = File(...),
    name: str = Form(...)
):
    file_path = f"{KNOWN_DIR}/{name}.jpg"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "message": f"{name} registered successfully"
    }


# ---------------- RECOGNIZE FACE ----------------
@app.post("/recognize-face")
async def recognize_face(file: UploadFile = File(...)):
    temp_path = f"{UPLOAD_DIR}/test.jpg"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = face_engine.recognize_face(temp_path)

    return {"result": result}