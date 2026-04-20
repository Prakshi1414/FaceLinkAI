from deepface import DeepFace
import os

KNOWN_DIR = "data/known_faces"


def recognize_face(image_path):
    try:
        # Compare with folder database
        result = DeepFace.find(
            img_path=image_path,
            db_path=KNOWN_DIR,
            enforce_detection=False,
            detector_backend="opencv"   # stable + fast
        )

        # No match found
        if len(result) == 0 or result[0].empty:
            return "No match found ❌"

        # Get matched file
        identity_path = result[0]["identity"].values[0]

        # Extract name from filename
        name = os.path.splitext(os.path.basename(identity_path))[0]

        return f"Matched: {name} ✅"

    except Exception as e:
        return f"Error: {str(e)}"