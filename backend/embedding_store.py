import os
import pickle
from deepface import DeepFace
import numpy as np

EMBEDDING_FILE = "data/embeddings.pkl"


def get_embedding(image_path):
    embedding = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet",
         detector_backend="opencv", 
        enforce_detection=False
    )[0]["embedding"]

    return np.array(embedding)


def load_db():
    if not os.path.exists(EMBEDDING_FILE):
        return []

    with open(EMBEDDING_FILE, "rb") as f:
        return pickle.load(f)


def save_db(data):
    with open(EMBEDDING_FILE, "wb") as f:
        pickle.dump(data, f)



def add_embedding(name, image_path, custom_path=None):
    db = load_db()
    
   
   
    target_path = custom_path if custom_path else image_path
    emb = get_embedding(target_path)

    db.append({
        "name": name,
        "image": image_path, 
        "embedding": emb
    })
    save_db(db)