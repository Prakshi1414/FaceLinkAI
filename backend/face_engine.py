from deepface import DeepFace
import numpy as np
import os

KNOWN_DIR = "data/known_faces"


def get_embedding(image_path):
    embedding = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet",
        enforce_detection=False
    )[0]["embedding"]

    return np.array(embedding)


def recognize_face(image_path):
    input_emb = get_embedding(image_path)

    best_match = None
    best_score = 1  # cosine distance

    for file in os.listdir(KNOWN_DIR):
        file_path = os.path.join(KNOWN_DIR, file)

        try:
            db_emb = get_embedding(file_path)

            # cosine similarity
            score = np.dot(input_emb, db_emb) / (
                np.linalg.norm(input_emb) * np.linalg.norm(db_emb)
            )

            if score > best_score:
                best_score = score
                best_match = file

        except:
            continue

    if best_match:
        name = best_match.split(".")[0]
        return f"Matched: {name} ✅"

    return "No match found "