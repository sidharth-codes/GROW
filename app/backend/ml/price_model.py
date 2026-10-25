"""
GROW – Market Price Forecasting (Task C)
=========================================
Assess whether market price data are sufficient for modelling, and implement
baseline and model-based forecasting ONLY if data are adequate.

DATA ADEQUACY ASSESSMENT
-------------------------
Market prices: dataset_status = 'awaiting_upload', 0 records.
No price observations are available in the current project state.

Decision: modelling is NOT attempted.
The pipeline:
  1. Checks for existing data.
  2. Reports exact status and data requirements.
  3. Persists assessment to models/market_price_model_meta.json.
  4. Defines the evaluation design for when data become available.

When data are uploaded (via the GROW UI or data/raw/market_prices/),
re-running this module will automatically execute the full forecasting pipeline.

PLANNED EVALUATION DESIGN (for future use)
-------------------------------------------
  Validation: walk-forward expanding-window cross-validation (no random split
               of time-series — future leakage must be prevented).
  Baselines  : seasonal naive (same month last year), rolling 4-week mean.
  Models     : Ridge regression on lagged features, Gradient Boosted Trees.
  Error unit : INR/quintal (interpretable price units, not normalised RMSE).
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.ml.utils import (
    read_csv_as_dicts,
    regression_metrics,
    save_model_with_meta,
)


ADEQUACY_THRESHOLD_RECORDS = 500
ADEQUACY_THRESHOLD_MONTHS = 24


def assess_price_data(price_csv: str = "data/processed/market_prices.csv") -> Dict[str, Any]:
    """Assess the market price dataset's suitability for forecasting."""
    if not os.path.exists(price_csv) or os.path.getsize(price_csv) == 0:
        return {
            "available": False,
            "record_count": 0,
            "reason": "market_prices.csv does not exist or is empty.",
        }

    records = read_csv_as_dicts(price_csv)
    if len(records) == 0:
        return {"available": False, "record_count": 0, "reason": "File has a header but 0 data rows."}

    dates = sorted(set(r["date"] for r in records))
    crops = set(r["crop"] for r in records)
    districts = set(r["district"] for r in records)
    n = len(records)
    n_months = len(set(d[:7] for d in dates))

    sufficient = n >= ADEQUACY_THRESHOLD_RECORDS and n_months >= ADEQUACY_THRESHOLD_MONTHS
    return {
        "available": True,
        "record_count": n,
        "distinct_crops": len(crops),
        "distinct_districts": len(districts),
        "date_range": f"{dates[0]} to {dates[-1]}",
        "distinct_months": n_months,
        "sufficient_for_modelling": sufficient,
        "threshold_records": ADEQUACY_THRESHOLD_RECORDS,
        "threshold_months": ADEQUACY_THRESHOLD_MONTHS,
    }


def run_walk_forward_cv(records: List[Dict], crop_filter: str) -> Dict:
    """Walk-forward cross-validation for a single crop.

    Uses an expanding training window: each fold adds one additional year.
    """
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import GradientBoostingRegressor

    crop_records = [r for r in records if r["crop"] == crop_filter]
    if len(crop_records) < 50:
        return {"error": f"Insufficient records for {crop_filter}: {len(crop_records)} < 50"}

    # Prepare monthly aggregates
    monthly: Dict[str, List[float]] = {}
    for r in crop_records:
        month_key = r["date"][:7]
        price = float(r.get("modal_price", 0))
        if price > 0:
            monthly.setdefault(month_key, []).append(price)

    months_sorted = sorted(monthly.keys())
    avg_by_month = {m: float(np.mean(v)) for m, v in monthly.items() if v}

    # Build lagged features: lag-1, lag-2, lag-12 (seasonal)
    feature_months = sorted(avg_by_month.keys())
    X_rows, y_vals = [], []
    for i, m in enumerate(feature_months):
        if i < 12:
            continue
        lag1 = avg_by_month.get(feature_months[i - 1])
        lag2 = avg_by_month.get(feature_months[i - 2])
        lag12 = avg_by_month.get(feature_months[i - 12])
        target = avg_by_month[m]
        if all(v is not None and v > 0 for v in [lag1, lag2, lag12]):
            X_rows.append([lag1, lag2, lag12])
            y_vals.append(target)

    if len(X_rows) < 20:
        return {"error": f"Insufficient lagged data rows for {crop_filter}: {len(X_rows)}"}

    X = np.array(X_rows, dtype=float)
    y = np.array(y_vals, dtype=float)

    # Walk-forward CV: first 60% train, then expand by 10% each fold
    n = len(X)
    fold_results = []
    min_train = int(n * 0.5)
    fold_size = max(5, int(n * 0.1))

    for start in range(min_train, n - fold_size, fold_size):
        X_train, y_train = X[:start], y[:start]
        X_test, y_test = X[start:start + fold_size], y[start:start + fold_size]

        # Seasonal naive baseline
        naive_pred = np.array([X_test[i, 2] for i in range(len(X_test))])  # lag-12
        naive_mae = float(np.mean(np.abs(y_test - naive_pred)))

        # Ridge
        ridge = Ridge(alpha=10.0)
        ridge.fit(X_train, y_train)
        ridge_pred = ridge.predict(X_test)
        ridge_mae = float(mean_absolute_error(y_test, ridge_pred))

        fold_results.append({
            "n_train": start,
            "n_test": len(y_test),
            "naive_mae": round(naive_mae, 2),
            "ridge_mae": round(ridge_mae, 2),
        })

    from sklearn.metrics import mean_absolute_error
    avg_naive = float(np.mean([f["naive_mae"] for f in fold_results]))
    avg_ridge = float(np.mean([f["ridge_mae"] for f in fold_results]))

    return {
        "crop": crop_filter,
        "n_samples": len(X),
        "n_folds": len(fold_results),
        "naive_seasonal_mae_avg": round(avg_naive, 2),
        "ridge_mae_avg": round(avg_ridge, 2),
        "folds": fold_results,
    }


def run_price_forecasting(output_dir: str = "models") -> dict:
    print("\n" + "=" * 70)
    print("TASK C: MARKET PRICE FORECASTING")
    print("=" * 70)

    assessment = assess_price_data()
    print("\nData adequacy assessment:")
    print(f"  Data available    : {assessment['available']}")
    print(f"  Record count      : {assessment['record_count']}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not assessment["available"] or assessment["record_count"] == 0:
        reason = assessment.get("reason", "No data")
        print(f"\n  STATUS: MODELLING DEFERRED — {reason}")
        print("\n  Market price data must be sourced from Agmarknet before models can be trained.")
        print("  See: data/raw/market_prices/market_prices_template.csv for required schema.")
        print("\n  Planned evaluation design when data become available:")
        print("    - Walk-forward expanding-window cross-validation")
        print("    - Seasonal naive baseline (same month prior year)")
        print("    - Ridge regression on lag-1, lag-2, lag-12 monthly averages")
        print("    - Error reported in INR/quintal (interpretable price units)")
        print("    - Minimum adequacy threshold: 500 records, 24 distinct months")

        meta = {
            "task": "market_price_forecasting",
            "status": "deferred_insufficient_data",
            "data_available": False,
            "record_count": 0,
            "reason": reason,
            "threshold_records": ADEQUACY_THRESHOLD_RECORDS,
            "threshold_months": ADEQUACY_THRESHOLD_MONTHS,
            "planned_validation": "walk_forward_expanding_window",
            "planned_baseline": "seasonal_naive_lag12",
            "planned_models": ["Ridge", "GradientBoostedTrees"],
            "error_unit": "INR/quintal",
            "data_source_url": "https://agmarknet.gov.in/PriceTrends/SA_Pri_Month.aspx",
            "upload_path": "data/raw/market_prices/",
            "template_path": "data/raw/market_prices/market_prices_template.csv",
        }
        meta_path = out / "market_price_model_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"\n  Assessment saved -> {meta_path}")
        return {"status": "deferred", "reason": reason}

    # If data are available
    records = read_csv_as_dicts("data/processed/market_prices.csv")
    crops_with_data = sorted(set(r["crop"] for r in records))
    print(f"\n  Crops available: {crops_with_data}")
    print(f"  Records: {len(records)}, Distinct months: {assessment['distinct_months']}")

    if not assessment["sufficient_for_modelling"]:
        print(f"\n  WARNING: Data below adequacy threshold "
              f"({assessment['record_count']} records < {ADEQUACY_THRESHOLD_RECORDS} required; "
              f"{assessment['distinct_months']} months < {ADEQUACY_THRESHOLD_MONTHS} required).")
        print("  Proceeding with limited modelling — results will have wide uncertainty.")

    cv_results = {}
    for crop in crops_with_data[:5]:  # limit to first 5 crops
        print(f"\n  Walk-forward CV for: {crop}")
        cv = run_walk_forward_cv(records, crop)
        if "error" in cv:
            print(f"    Skipped: {cv['error']}")
        else:
            print(f"    Folds: {cv['n_folds']}, "
                  f"Naive MAE: {cv['naive_seasonal_mae_avg']:.2f} INR/q, "
                  f"Ridge MAE: {cv['ridge_mae_avg']:.2f} INR/q")
            cv_results[crop] = cv

    meta = {
        "task": "market_price_forecasting",
        "status": "evaluated",
        "data_available": True,
        "record_count": assessment["record_count"],
        "sufficient_for_modelling": assessment["sufficient_for_modelling"],
        "cross_validation_results": cv_results,
        "validation_design": "walk_forward_expanding_window",
        "error_unit": "INR/quintal",
    }
    meta_path = out / "market_price_model_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"\n  Results saved -> {meta_path}")
    return {"status": "evaluated", "cv_results": cv_results}


if __name__ == "__main__":
    run_price_forecasting()
