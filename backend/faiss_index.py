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
      
        return

    embeddings = []
    names = []
    images = []

    for item in db:
        embeddings.append(item["embedding"])
        names.append(item["name"])
        images.append(item["image"])

    X = np.array(embeddings).astype("float32")

   
    faiss.normalize_L2(X)

    dimension = X.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(X)

    print("✅ INDEX BUILT:", index.ntotal)


def search_face(query_embedding):
    global index, names, images


    if index is None:
        build_index()

 
    if index is None:
     
        return []

    query = np.array([query_embedding]).astype("float32")

  
    faiss.normalize_L2(query)


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