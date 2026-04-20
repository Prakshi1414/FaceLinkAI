from deepface import DeepFace
import numpy as np
import os

KNOWN_DIR = "data/known_faces"

def get_embedding(image_path):
    embedding = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet",
        enforce_detection=False,
        detector_backend="opencv"
    )[0]["embedding"]

    return np.array(embedding)


def recognize_face(image_path):
    input_emb = get_embedding(image_path)

    best_match = None
    best_score = -1  # cosine distance

    for file in os.listdir(KNOWN_DIR):
        file_path = os.path.join(KNOWN_DIR, file)

        try:
            db_emb = get_embedding(file_path)

            # cosine similarity
            score = np.dot(input_emb, db_emb) / (
                np.linalg.norm(input_emb) * np.linalg.norm(db_emb)
            )

            print("Comparing", file, "Score:", score)

            if score > best_score:
                best_score = score
                best_match = file

        except Exception as e:
            print("Error:", file, e)
            continue

    if best_match and best_score > 0.6:
        name = best_match.split(".")[0]
        return f"Matched: {name} ✅ (score={best_score})"

    return "No match found "