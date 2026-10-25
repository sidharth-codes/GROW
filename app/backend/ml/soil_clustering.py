"""
GROW – Soil/Region Clustering (Task A)
=======================================
Cluster Kerala's 23 soil-profile records using KMeans and hierarchical
agglomerative clustering.

DATA ADEQUACY NOTE
------------------
- 23 soil records across 13 districts.
- Features are entirely categorical (texture, drainage, pH, organic matter).
- Small sample: clustering reveals broad agro-climatic groups, not precise
  soil classes.  Cluster IDs are NOT quality rankings.
- Results are interpretive labels; they are NOT ML predictions.
"""

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.ml.utils import (
    OrdinalEncoder,
    read_csv_as_dicts,
    save_model_with_meta,
)


# Human-readable cluster label suggestions (assigned post-hoc after inspecting centroids)
CLUSTER_LABELS = {
    0: "Lowland Hydromorphic",
    1: "Laterite Upland",
    2: "Alluvial Midland",
    3: "High-Range Forest",
    4: "Coastal Sandy",
}

FEATURE_COLUMNS = [
    "soil_texture",
    "drainage",
    "ph_category",
    "organic_matter_category",
    "fertility_category",
]


def load_and_encode_soil(soil_csv: str = "data/processed/soil.csv"):
    records = read_csv_as_dicts(soil_csv)
    raw_features = [[r[c] for c in FEATURE_COLUMNS] for r in records]
    enc = OrdinalEncoder()
    X = enc.fit_transform(raw_features)
    return records, X, enc


def choose_k(X: np.ndarray, k_range=(2, 7)) -> dict:
    """Evaluate silhouette scores to choose k."""
    scores = {}
    for k in range(k_range[0], k_range[1] + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = km.fit_predict(X)
        if len(set(labels)) > 1:
            scores[k] = round(silhouette_score(X, labels), 4)
    return scores


def run_clustering(output_dir: str = "models") -> dict:
    """Run soil clustering and persist model."""
    print("\n" + "=" * 70)
    print("TASK A: SOIL / REGION CLUSTERING")
    print("=" * 70)
    print("\nData adequacy assessment:")
    print("  - 23 soil records, 13 districts, 5 categorical features")
    print("  - Sample is small; clustering reveals broad groups only")
    print("  - Cluster IDs carry no inherent agronomic quality ranking")
    print("  - Results are INTERPRETIVE, not trained predictions")

    records, X, enc = load_and_encode_soil()

    # Select optimal k by silhouette
    print("\nSilhouette scores by k:")
    sil_scores = choose_k(X, k_range=(2, 6))
    for k, s in sorted(sil_scores.items()):
        print(f"    k={k}  silhouette={s:.4f}")
    best_k = max(sil_scores, key=sil_scores.get)
    print(f"\nSelected k={best_k} (highest silhouette={sil_scores[best_k]:.4f})")

    km = KMeans(n_clusters=best_k, random_state=42, n_init=20)
    km_labels = km.fit_predict(X)

    # Also run Agglomerative for comparison
    agg = AgglomerativeClustering(n_clusters=best_k)
    agg_labels = agg.fit_predict(X)
    agg_sil = silhouette_score(X, agg_labels) if len(set(agg_labels)) > 1 else float("nan")

    print(f"\nAgglomerative clustering silhouette (k={best_k}): {agg_sil:.4f}")

    # Print cluster membership
    cluster_members: dict = {i: [] for i in range(best_k)}
    for i, r in enumerate(records):
        cluster_members[km_labels[i]].append(f"{r['district']} ({r['soil_type']})")

    print("\nKMeans cluster assignments:")
    for cid, members in cluster_members.items():
        label = CLUSTER_LABELS.get(cid, f"Cluster {cid}")
        print(f"  Cluster {cid} [{label}]:")
        for m in members:
            print(f"    - {m}")

    # Save model + encoder
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    save_model_with_meta(
        {"kmeans": km, "encoder": enc, "feature_columns": FEATURE_COLUMNS},
        str(out / "soil_clustering.joblib"),
        meta={
            "task": "soil_region_clustering",
            "algorithm": "KMeans",
            "k": best_k,
            "silhouette": sil_scores[best_k],
            "agglomerative_silhouette": agg_sil,
            "n_records": len(records),
            "n_features": len(FEATURE_COLUMNS),
            "feature_columns": FEATURE_COLUMNS,
            "data_adequacy": "LOW - 23 records, 5 categorical features. Results are indicative groupings only.",
            "interpretation_warning": "Cluster IDs are not quality rankings and must not be treated as ML predictions.",
        },
    )

    return {
        "k": best_k,
        "silhouette": sil_scores[best_k],
        "cluster_members": {str(k): v for k, v in cluster_members.items()},
        "silhouette_by_k": sil_scores,
        "data_adequacy": "LOW",
    }


if __name__ == "__main__":
    run_clustering()
