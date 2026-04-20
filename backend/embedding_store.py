from deepface import DeepFace
import numpy as np

def get_embedding(image_path):
    try:
        print("Embedding for:", image_path)

        embedding = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",
            enforce_detection=False
        )

        print("RAW OUTPUT:", embedding)

        return np.array(embedding[0]["embedding"])

    except Exception as e:
        print("EMBEDDING ERROR:", image_path, e)
        return None