"""Run all GROW ML tasks in sequence."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.backend.ml.soil_clustering import run_clustering
from app.backend.ml.yield_model import run_yield_prediction
from app.backend.ml.price_model import run_price_forecasting

if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# GROW MACHINE LEARNING TRAINING RUN")
    print("#" * 70)

    clustering_results = run_clustering(output_dir="models")
    yield_results = run_yield_prediction(output_dir="models")
    price_results = run_price_forecasting(output_dir="models")

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Task A (Soil Clustering) : k={clustering_results['k']}, "
          f"silhouette={clustering_results['silhouette']:.4f}, adequacy=LOW")

    best_mae = min(v["mae"] for v in yield_results.values())
    best_model = min(yield_results, key=lambda k: yield_results[k]["mae"])
    print(f"  Task B (Yield Prediction): best={best_model}, "
          f"test MAE={best_mae:.0f} kg/ha, adequacy=MODERATE")

    print(f"  Task C (Price Forecast)  : status={price_results['status'].upper()}, "
          f"adequacy=INSUFFICIENT (no data uploaded yet)")
