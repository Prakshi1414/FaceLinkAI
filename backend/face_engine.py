
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

def recognize_faces(image_path, auto_save=True):
    db_records = load_db()
    final_results = []
    
    file_hash = get_image_hash(image_path)
    file_ext = os.path.splitext(image_path)[1]
    permanent_name = f"{file_hash}{file_ext}"
    permanent_path = os.path.join("data/images", permanent_name)
    
    '''
         existing_file_entry = next((x for x in db_records if x["image"] == permanent_path), None)

    if existing_file_entry:
        # Agar file mil gayi, toh aage mat badho, purana data return kar do
        name = existing_file_entry["name"]
        emb_data = existing_file_entry["embedding"]
        serializable_emb = emb_data.tolist() if hasattr(emb_data, 'tolist') else emb_data
        all_photos = list(([x["image"] for x in db_records if x["name"] == name]))
        return [{
            "person": name, 
            "images": all_photos, 
            "status": "existing",
           "embedding": serializable_emb,
            "already_known": True # Flag for logic
        }]'''
    if not os.path.exists(permanent_path):
        shutil.copy(image_path, permanent_path)
    
    faces = extract_faces(permanent_path)
    new_face_added = False # Index management ke liye

    for i, face in enumerate(faces):
        face_img = face.get("face")
        if face_img is None or face_img.size == 0: continue

        face_img = (face_img * 255).astype(np.uint8)
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        temp_crop = f"temp/face_{i}.jpg"
        cv2.imwrite(temp_crop, face_img)

        emb = get_embedding(temp_crop)
        if emb is None: continue
        
        results = search_face(emb)
        filtered = [r for r in results if r["score"] > 0.60] 

        if filtered:
            name = filtered[0]["name"]
            existing_paths = [x["image"] for x in db_records if x["name"] == name]
            
            # PROBLEM YAHAN THI: Check toh ho raha tha, par save nahi
            if permanent_path not in existing_paths:
                # Agar auto_save ON hai, toh is nayi photo (group/single) ko link karein
                if auto_save:
                    add_embedding(name, emb, permanent_path) # <--- YE LINE MISSING THI
                    db_records = load_db() # Naya data refresh karein

            # Ab yahan 'all_photos' mein purani aur nayi dono images milengi
            all_photos = list(set([x["image"] for x in db_records if x["name"] == name]))
            
            final_results.append({
                "person": name, 
                "images": all_photos, 
                "status": "existing",
                "embedding": emb.tolist() if hasattr(emb, 'tolist') else emb
            })
            
        else:
            new_name = f"user_{uuid.uuid4().hex[:6]}"
            if auto_save:
                add_embedding(new_name, emb, permanent_path)
                db_records = load_db()
                new_face_added = True
            
            final_results.append({
                "person": new_name, 
                "images": [permanent_path], 
                "status": "new",
                "embedding": emb.tolist() if hasattr(emb, 'tolist') else emb     # FIX: KeyError se bachega
            })

    if new_face_added:
        build_index() # Loop ke bahar sirf ek baar call karein
            
    return final_results


def extract_faces(image_path):
    faces = DeepFace.extract_faces(
        img_path=image_path,
        detector_backend="opencv",
        enforce_detection=False
    )
    return faces    