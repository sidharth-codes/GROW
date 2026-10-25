"""
GROW – Crop Yield Prediction (Task B)
======================================
Predict district-level annual crop yield (kg/ha) using historical DES Kerala
statistics joined with NASA POWER seasonal weather aggregates.

DATA ADEQUACY ASSESSMENT (run before modelling)
-------------------------------------------------
Yield dataset  : 6,422 rows, 22 crops, 14 districts, 2001-02 to 2023-24
Weather dataset: 56,252 daily rows, 14 districts, 2015-01-01 to 2025-12-31
Weather overlap: yields from 2015-16 onward can be joined to weather; that
                 is 9 yield-years × 22 crops × 14 districts ≈ 2,772 records
                 maximum (minus crops not grown in a district in a year).

VALIDATION DESIGN
-----------------
Time-aware split: test set = the 4 most recent agricultural years (2019-20
to 2023-24).  Training set = 2015-16 to 2018-19.
Random shuffle is NOT used — that would leak future information.

FEATURES
--------
  - crop (label-encoded)
  - district (label-encoded)
  - year_index (integer — 0 for 2015-16, 1 for 2016-17 …)
  - annual_rainfall_mm (sum of daily PRECTOTCORR for calendar year)
  - mean_tmax_c (mean of daily T2M_MAX)
  - mean_tmin_c (mean of daily T2M_MIN)
  - mean_rh_percent (mean of daily RH2M)

TARGET : yield_kg_per_hectare

BASELINES
---------
  1. District-crop historical mean (training set mean)
  2. Random Forest Regressor
  3. Ridge Regression

No target leakage: area and production (from which yield is derived) are
excluded from the feature set.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.ml.utils import (
    OrdinalEncoder,
    read_csv_as_dicts,
    save_model_with_meta,
    regression_metrics,
    time_aware_split,
)

# Agricultural year to calendar year mapping (e.g. "2015-16" → 2015)
def ag_year_to_int(ag_year: str) -> int:
    return int(ag_year.split("-")[0])


# ── Weather aggregation ─────────────────────────────────────────────────────

def build_weather_annual_aggs(weather_csv: str = "data/processed/weather.csv") -> Dict[Tuple[str, int], Dict]:
    """Compute per-district per-calendar-year weather statistics."""
    aggs: Dict[Tuple[str, int], Dict] = defaultdict(lambda: {
        "rainfall_sum": 0.0, "tmax_vals": [], "tmin_vals": [], "rh_vals": [], "n": 0
    })
    with open(weather_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            district = row["district"]
            year = int(row["date"][:4])
            key = (district, year)
            aggs[key]["rainfall_sum"] += float(row["rainfall_mm"])
            aggs[key]["tmax_vals"].append(float(row["temperature_max_c"]))
            aggs[key]["tmin_vals"].append(float(row["temperature_min_c"]))
            aggs[key]["rh_vals"].append(float(row["humidity_percent"]))
            aggs[key]["n"] += 1

    result = {}
    for key, v in aggs.items():
        if v["n"] > 0:
            result[key] = {
                "annual_rainfall_mm": round(v["rainfall_sum"], 2),
                "mean_tmax_c": round(float(np.mean(v["tmax_vals"])), 3),
                "mean_tmin_c": round(float(np.mean(v["tmin_vals"])), 3),
                "mean_rh_percent": round(float(np.mean(v["rh_vals"])), 3),
            }
    return result


# ── Dataset assembly ─────────────────────────────────────────────────────────

def assemble_dataset(
    yield_csv: str = "data/processed/crop_yield.csv",
    weather_csv: str = "data/processed/weather.csv",
    min_year: int = 2015,
) -> List[Dict]:
    """Join yield and weather records into a unified ML dataset."""
    weather_aggs = build_weather_annual_aggs(weather_csv)
    records = []

    with open(yield_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cal_year = ag_year_to_int(row["year"])
            if cal_year < min_year:
                continue
            district = row["district"]
            weather_key = (district, cal_year)
            if weather_key not in weather_aggs:
                continue
            w = weather_aggs[weather_key]
            yld = float(row["yield_kg_per_hectare"])
            if yld <= 0:
                continue
            records.append({
                "year": row["year"],
                "crop": row["crop"],
                "district": district,
                "yield_kg_per_hectare": yld,
                "annual_rainfall_mm": w["annual_rainfall_mm"],
                "mean_tmax_c": w["mean_tmax_c"],
                "mean_tmin_c": w["mean_tmin_c"],
                "mean_rh_percent": w["mean_rh_percent"],
            })
    return records


# ── Feature matrix builder ────────────────────────────────────────────────────

def build_feature_matrix(records: List[Dict], enc: OrdinalEncoder = None, fit: bool = True):
    """Return (X, y, encoder)."""
    base_year = 2015
    raw_cat = [[r["crop"], r["district"]] for r in records]
    num_feats = np.array([
        [
            ag_year_to_int(r["year"]) - base_year,
            r["annual_rainfall_mm"],
            r["mean_tmax_c"],
            r["mean_tmin_c"],
            r["mean_rh_percent"],
        ]
        for r in records
    ], dtype=float)

    if enc is None:
        enc = OrdinalEncoder()
    if fit:
        cat_encoded = enc.fit_transform(raw_cat)
    else:
        cat_encoded = enc.transform(raw_cat)

    X = np.hstack([cat_encoded, num_feats])
    y = np.array([r["yield_kg_per_hectare"] for r in records])
    return X, y, enc


# ── Baseline: district-crop mean ─────────────────────────────────────────────

def build_mean_baseline(train_records: List[Dict]) -> Dict:
    means: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for r in train_records:
        means[(r["crop"], r["district"])].append(r["yield_kg_per_hectare"])
    return {k: float(np.mean(v)) for k, v in means.items()}


def predict_mean_baseline(records: List[Dict], means: Dict) -> np.ndarray:
    global_mean = float(np.mean(list(means.values())))
    return np.array([
        means.get((r["crop"], r["district"]), global_mean)
        for r in records
    ])


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_yield_prediction(output_dir: str = "models") -> dict:
    print("\n" + "=" * 70)
    print("TASK B: CROP YIELD PREDICTION")
    print("=" * 70)

    # Data adequacy assessment
    print("\nData adequacy assessment:")
    dataset = assemble_dataset()
    n = len(dataset)
    crops_found = sorted(set(r["crop"] for r in dataset))
    years_found = sorted(set(r["year"] for r in dataset))
    print(f"  Joined records (2015-16 onwards, weather available): {n}")
    print(f"  Crops: {len(crops_found)}")
    print(f"  Years: {years_found[0]} to {years_found[-1]}")
    print(f"  Train/test split: time-aware (test = last 4 agri-years)")

    if n < 50:
        print("  WARNING: Fewer than 50 joinable records — models will have high uncertainty.")

    # Time-aware train/test split
    train_recs, test_recs = time_aware_split(dataset, year_key="year", test_ratio=0.4)
    train_years = sorted(set(r["year"] for r in train_recs))
    test_years = sorted(set(r["year"] for r in test_recs))
    print(f"\n  Training years ({len(train_recs)} records): {train_years[0]} to {train_years[-1]}")
    print(f"  Test years     ({len(test_recs)} records):  {test_years[0]} to {test_years[-1]}")

    # Build feature matrices
    X_train, y_train, enc = build_feature_matrix(train_recs, fit=True)
    X_test, y_test, _ = build_feature_matrix(test_recs, enc=enc, fit=False)

    # Scale numeric features (columns 2 onwards are numeric; 0,1 are categorical ordinals)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    results = {}

    # ── Baseline: district-crop mean ──────────────────────────────────────────
    print("\n--- Baseline: District-Crop Historical Mean ---")
    means = build_mean_baseline(train_recs)
    bl_pred = predict_mean_baseline(test_recs, means)
    results["baseline_district_crop_mean"] = regression_metrics(
        y_test, bl_pred, unit="kg/ha", model_name="Baseline"
    )

    # ── Ridge Regression ─────────────────────────────────────────────────────
    print("\n--- Ridge Regression ---")
    ridge = Ridge(alpha=10.0)
    ridge.fit(X_train_s, y_train)
    ridge_pred = ridge.predict(X_test_s)
    results["ridge_regression"] = regression_metrics(
        y_test, ridge_pred, unit="kg/ha", model_name="Ridge"
    )

    # ── Random Forest ────────────────────────────────────────────────────────
    print("\n--- Random Forest (n_estimators=200) ---")
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    results["random_forest"] = regression_metrics(
        y_test, rf_pred, unit="kg/ha", model_name="RandomForest"
    )

    # ── Feature importances ──────────────────────────────────────────────────
    feat_names = ["crop_enc", "district_enc", "year_index",
                  "annual_rainfall_mm", "mean_tmax_c", "mean_tmin_c", "mean_rh_percent"]
    importances = dict(zip(feat_names, rf.feature_importances_.tolist()))
    print("\n  Feature importances (Random Forest):")
    for fn, fi in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"    {fn:30s}: {fi:.4f}")

    # Model selection: pick best by test MAE
    best_name = min(
        results,
        key=lambda k: results[k]["mae"] if np.isfinite(results[k]["mae"]) else 1e9,
    )
    print(f"\n  Best model by test MAE: {best_name}")

    # ── Persist best model ────────────────────────────────────────────────────
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    meta = {
        "task": "crop_yield_prediction",
        "best_model": best_name,
        "n_train": len(train_recs),
        "n_test": len(test_recs),
        "train_years": f"{train_years[0]} to {train_years[-1]}",
        "test_years": f"{test_years[0]} to {test_years[-1]}",
        "feature_columns": feat_names,
        "metrics": results,
        "feature_importances": importances,
        "data_adequacy": (
            "MODERATE — 9 weather-joined agricultural years (2015-24). "
            "Model captures cross-crop and district differences but has limited temporal depth. "
            "Confidence intervals are wide; forecasts should be presented as indicative ranges."
        ),
        "validation_design": (
            "Time-aware split: test = 4 most recent agri-years; no random shuffle. "
            "Target leakage excluded: area and production not in feature set."
        ),
    }

    save_model_with_meta(
        {"random_forest": rf, "ridge": ridge, "scaler": scaler,
         "encoder": enc, "baseline_means": means},
        str(out / "crop_yield_model.joblib"),
        meta=meta,
    )

    return results


if __name__ == "__main__":
    run_yield_prediction()
