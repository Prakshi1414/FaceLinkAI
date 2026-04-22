import faiss
import numpy as np
from backend.embedding_store import load_db

index = None
names = []
images = []


def build_index():
    global index, names, images

    db = load_db()

    if len(db) == 0:
        print("❌ DB empty")
        return

    embeddings = []
    names = []
    images = []

    for item in db:
        embeddings.append(item["embedding"])
        names.append(item["name"])
        images.append(item["image"])

    X = np.array(embeddings).astype("float32")

    # 🔥 VERY IMPORTANT
    faiss.normalize_L2(X)

    dimension = X.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(X)

    print("✅ INDEX BUILT:", index.ntotal)


def search_face(query_embedding):
    global index, names, images

    # Agar index load nahi hai, toh load karne ki koshish karo
    if index is None:
        build_index()

    #  FIX: Agar DB khali hone ki wajah se build_index ne index create nahi kiya
    if index is None:
        print(" Search skip ho gaya kyunki database abhi khali hai.")
        return []

    query = np.array([query_embedding]).astype("float32")

    # 🔥 VERY IMPORTANT
    faiss.normalize_L2(query)

    # Safely search
    scores, indices = index.search(query, k=5)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:
            continue

        results.append({
            "name": names[idx],
            "image": images[idx],
            "score": float(scores[0][i])
        })

    return results