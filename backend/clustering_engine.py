import os
import numpy as np
from sklearn.cluster import DBSCAN
from backend.embedding_store import get_embedding


DATASET_DIR = "data/known_faces"


def build_embeddings():
    embeddings = []
    image_paths = []

    for file in os.listdir(DATASET_DIR):
        if not file.lower().endswith((".jpg", ".jpeg", ".png")):
         continue

        path = os.path.join(DATASET_DIR, file)
        print("Processing:", file)  

        try:
            emb = get_embedding(path)

            if emb is None:
              print("Skipping:", file)
              continue

            embeddings.append(emb)
            image_paths.append(file)
        except:
            continue

    return np.array(embeddings), image_paths


def run_clustering():
    embeddings, image_paths = build_embeddings()
    print("TOTAL IMAGES:", len(image_paths))
    print("TOTAL EMBEDDINGS:", len(embeddings))
    print("EMBEDDING SHAPE:", embeddings.shape)

    if len(embeddings) == 0:
        return "No faces found"

    clustering = DBSCAN(
    eps=0.7,
    min_samples=1,
    metric="cosine"
    ).fit(embeddings)

    labels = clustering.labels_

    clustered_data = {}

    for label, file in zip(labels, image_paths):
        print(label, file)
        if label == -1:
            continue  # noise skip

        folder = f"person_{label}"

        if folder not in clustered_data:
            clustered_data[folder] = []

        clustered_data[folder].append(file)

    return clustered_data