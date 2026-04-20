import numpy as np
from sklearn.cluster import DBSCAN

def cluster_faces(embeddings):
    clustering = DBSCAN(
        eps=0.5,
        min_samples=2,  
        metric="cosine"
    ).fit(embeddings)

    return clustering.labels_