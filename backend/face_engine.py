
from backend.embedding_store import get_embedding, add_embedding, load_db
from backend.faiss_index import build_index, search_face
from deepface import DeepFace
import numpy as np
import uuid
import cv2


def recognize_faces(image_path):
    faces = extract_faces(image_path)

    final_results = []

    # 🔥 SINGLE FACE → same old flow
    if len(faces) == 1:
        emb = get_embedding(image_path)
        results = search_face(emb)

        filtered = [r for r in results if r["score"] > 0.5]

        if filtered:
            name = filtered[0]["name"]

            db = load_db()
            images = [x["image"] for x in db if x["name"] == name]

            return [{
                "person": name,
                "images": images
            }]
        else:
           
            new_name = f"user_{uuid.uuid4().hex[:6]}"
            add_embedding(new_name, image_path)
            build_index()

            return [{
                "person": new_name,
                "images": [image_path],
                "status": "new"
            }]

    # 🔥 MULTI FACE
    for i, face in enumerate(faces):
 
        face_img = face.get("face")   #  SAFE ACCESS

        if face_img is None or face_img.size == 0:
            continue

        #  convert properly
        face_img = (face_img * 255).astype(np.uint8)

    
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)

        temp_path = f"temp/face_{i}.jpg"
        cv2.imwrite(temp_path, face_img)

        #  embedding + search
        emb = get_embedding(temp_path)
        results = search_face(emb)

        filtered = [r for r in results if r["score"] > 0.7]

        if filtered:
            name = filtered[0]["name"]

            db = load_db()
            images = [x["image"] for x in db if x["name"] == name]

            final_results.append({
                "person": name,
                "images": images
            })

        else:
            new_name = f"user_{uuid.uuid4().hex[:6]}"
            add_embedding(new_name, temp_path)
            build_index()   

            final_results.append({
                "person": new_name,
                "images": [temp_path],
                "status": "new"
            })

    return final_results

    

def extract_faces(image_path):
    faces = DeepFace.extract_faces(
        img_path=image_path,
        detector_backend="opencv",
        enforce_detection=False
    )
    return faces