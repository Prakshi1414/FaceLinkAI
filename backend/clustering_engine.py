from sklearn.cluster import DBSCAN
import numpy as np
from backend.embedding_store import load_db
from backend.embedding_store import update_name_in_db
import os

def perform_clustering():
    # 1. Database se saara data load karein
    db_records = load_db()
    if not db_records:
        return "No data found in database"

    # 2. Embeddings ko array mein convert karein
    embeddings = [np.array(record["embedding"]) for record in db_records]
    embeddings = np.array(embeddings)

    # 3. DBSCAN Algorithm (eps: kitni doori par group banana hai, min_samples: kam se kam kitni photos)
    # eps 0.35 se 0.45 ke beech best kaam karta hai Face recognition ke liye
    clustering_model = DBSCAN(eps=0.35, min_samples=2, metric="cosine")
    labels = clustering_model.fit_predict(embeddings)

    # 4. Results ko organize karein
    clusters = {}
    for i, label in enumerate(labels):
        label_key = str(label) if label != -1 else "Unknown" # -1 matlab Noise/Single photo
        if label_key not in clusters:
            clusters[label_key] = []
        
        clusters[label_key].append({
            "name": db_records[i]["name"],
            "image": db_records[i]["image"]
        })
    
    return clusters

def auto_merge_clusters(clusters):
    summary = {"updated": 0, "merged_groups": 0}
    
    for cluster_id, members in clusters.items():
        if cluster_id == "Unknown": continue # Noise ko chhod dein

        # 1. Check karein kya is group mein koi "Known Name" hai?
        # (Hum maante hain ki 'user_' se shuru hone wale temporary names hain)
        known_names = [m["name"] for m in members if not m["name"].startswith("user_")]
        
        if known_names:
            # Sabse zyada baar aane wala naam pick karein (Best Name)
            best_name = max(set(known_names), key=known_names.count)
        else:
            # Agar koi known name nahi hai, toh cluster ID ke hisab se ek unique name banayein
            best_name = f"Group_Person_{cluster_id}"

        # 2. Database mein updates bhejein
        for member in members:
            if member["name"] != best_name:
                # Sirf unhe update karein jinka naam best_name se alag hai
                update_name_in_db(member["image"], best_name)
                summary["updated"] += 1
        
        summary["merged_groups"] += 1
        
    return summary