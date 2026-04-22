
from backend.embedding_store import get_embedding, add_embedding, load_db
from backend.faiss_index import build_index, search_face
from deepface import DeepFace
import numpy as np
import shutil
import os
import hashlib 
import uuid
import cv2

def get_image_hash(image_path):
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def recognize_faces(image_path):
    db_records = load_db()
    final_results = []
    
    # --- STEP 1: Loop se pehle sirf EK baar file handle karein ---
    file_hash = get_image_hash(image_path)
    file_ext = os.path.splitext(image_path)[1]
    # Unique name based on Hash (No UUID here to prevent duplicates)
    permanent_name = f"{file_hash}{file_ext}"
    permanent_path = os.path.join("data/images", permanent_name)
    
    # Agar ye exact file pehle se folder mein nahi hai, tabhi copy karein
    if not os.path.exists(permanent_path):
        shutil.copy(image_path, permanent_path)
    
    # --- STEP 2: Ab scanning shuru karein ---
    faces = extract_faces(permanent_path)

    for i, face in enumerate(faces):
        face_img = face.get("face")
        if face_img is None or face_img.size == 0: continue

        # Face cropping for embedding
        face_img = (face_img * 255).astype(np.uint8)
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        temp_crop = f"temp/face_{i}.jpg"
        cv2.imwrite(temp_crop, face_img)

        emb = get_embedding(temp_crop)
        if emb is None: continue
        
        results = search_face(emb)
        filtered = [r for r in results if r["score"] > 0.75]

        if filtered:
            #  EXISTING PERSON
            name = filtered[0]["name"]
            
            # Check karein kya ye permanent_path is bande se linked hai?
            existing_paths = [x["image"] for x in db_records if x["name"] == name]
            
            if permanent_path not in existing_paths:
                add_embedding(name, emb, permanent_path)
                db_records = load_db() # Refresh data

            all_photos = list(set([x["image"] for x in db_records if x["name"] == name]))
            final_results.append({"person": name, "images": all_photos, "status": "existing"})
            
        else:
            # ✨ NEW PERSON
            new_name = f"user_{uuid.uuid4().hex[:6]}"
            
            # Naye bande ko usi permanent_path se link karein jo upar banaya tha
            add_embedding(new_name, emb, permanent_path)
            build_index()
            db_records = load_db()
            
            final_results.append({"person": new_name, "images": [permanent_path], "status": "new"})
            
    return final_results


def extract_faces(image_path):
    faces = DeepFace.extract_faces(
        img_path=image_path,
        detector_backend="opencv",
        enforce_detection=False
    )
    return faces    