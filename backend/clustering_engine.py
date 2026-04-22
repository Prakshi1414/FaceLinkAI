import numpy as np
from sklearn.cluster import DBSCAN
from backend.embedding_store import load_db # Seedha DB se load karein

def run_clustering():
    db_data = load_db()
    if not db_data:
        return "No data in database"

    # Extract embeddings and names
    embeddings = np.array([item["embedding"] for item in db_data]).astype("float32")
    names = [item["name"] for item in db_data]

    # DBSCAN Clustering
    clustering = DBSCAN(eps=0.6, min_samples=2, metric="cosine").fit(embeddings)
    labels = clustering.labels_

    clusters = {}
    for label, name in zip(labels, names):
        key = f"Cluster_{label}" if label != -1 else "Unknown_Noise"
        if key not in clusters:
            clusters[key] = []
        if name not in clusters[key]:
            clusters[key].append(name)

    return clusters