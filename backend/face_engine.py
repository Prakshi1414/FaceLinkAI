
from backend.embedding_store import get_embedding
from backend.faiss_index import search_face


def recognize_face(image_path):
    input_emb = get_embedding(image_path)
    results = search_face(input_emb)

   
    filtered = [r for r in results if r["score"] > 0.5]

    if filtered:
        return {"matches": filtered}

    return {"matches": [], "message": "No good match found"}
