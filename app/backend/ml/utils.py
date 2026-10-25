"""
GROW Machine Learning Infrastructure
=====================================
Shared utilities: feature encoders, time-aware splitters, metric reporters,
and model persistence helpers.  No pandas dependency.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.preprocessing import LabelEncoder


# ---------------------------------------------------------------------------
# CSV helpers (no pandas)
# ---------------------------------------------------------------------------

def read_csv_as_dicts(path: str) -> List[Dict[str, str]]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def safe_float(value: str, default: float = 0.0) -> float:
    try:
        v = float(str(value).replace(",", "").strip())
        return v if np.isfinite(v) else default
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Ordinal encoder for categorical features
# ---------------------------------------------------------------------------

class OrdinalEncoder:
    """Encodes string categories to integer codes; handles unseen labels."""

    def __init__(self):
        self.categories_: Dict[int, List[str]] = {}
        self._fitted = False

    def fit_transform(self, X: List[List[Any]]) -> np.ndarray:
        arr = np.array(X, dtype=object)
        result = np.zeros(arr.shape, dtype=float)
        for col_idx in range(arr.shape[1]):
            col = arr[:, col_idx].tolist()
            unique = list(dict.fromkeys(str(v) for v in col))
            self.categories_[col_idx] = unique
            lookup = {v: i for i, v in enumerate(unique)}
            result[:, col_idx] = [lookup.get(str(v), -1) for v in col]
        self._fitted = True
        return result

    def transform(self, X: List[List[Any]]) -> np.ndarray:
        arr = np.array(X, dtype=object)
        result = np.zeros(arr.shape, dtype=float)
        for col_idx in range(arr.shape[1]):
            lookup = {v: i for i, v in enumerate(self.categories_.get(col_idx, []))}
            col = arr[:, col_idx].tolist()
            result[:, col_idx] = [lookup.get(str(v), -1) for v in col]
        return result


# ---------------------------------------------------------------------------
# Time-aware train/test split
# ---------------------------------------------------------------------------

def time_aware_split(
    records: List[Dict],
    year_key: str,
    test_ratio: float = 0.2,
) -> Tuple[List[Dict], List[Dict]]:
    """Split records so test set contains only the most recent years.

    This prevents future data from leaking into the training set — essential
    for time-series agricultural statistics.
    """
    years_sorted = sorted(set(r[year_key] for r in records))
    n_test_years = max(1, int(len(years_sorted) * test_ratio))
    test_years = set(years_sorted[-n_test_years:])
    train = [r for r in records if r[year_key] not in test_years]
    test = [r for r in records if r[year_key] in test_years]
    return train, test


# ---------------------------------------------------------------------------
# Regression metric reporter
# ---------------------------------------------------------------------------

def regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    unit: str = "",
    model_name: str = "",
) -> Dict[str, float]:
    """Return and print standard regression evaluation metrics."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)

    # Mean Absolute Percentage Error (guarded against zero targets)
    nonzero = y_true != 0
    mape = float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100) if nonzero.any() else float("nan")

    suffix = f" {unit}" if unit else ""
    label = f"[{model_name}] " if model_name else ""
    print(f"  {label}MAE  = {mae:.2f}{suffix}")
    print(f"  {label}RMSE = {rmse:.2f}{suffix}")
    print(f"  {label}R²   = {r2:.4f}")
    print(f"  {label}MAPE = {mape:.1f}%")
    return {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


# ---------------------------------------------------------------------------
# Model persistence with metadata
# ---------------------------------------------------------------------------

def save_model_with_meta(
    model: Any,
    model_path: str,
    meta: Dict[str, Any],
    meta_path: Optional[str] = None,
) -> None:
    import joblib
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    if meta_path is None:
        meta_path = str(model_path).replace(".joblib", "_meta.json")
    meta["saved_at"] = datetime.now().isoformat()
    meta["model_file"] = str(model_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"  Model saved  -> {model_path}")
    print(f"  Metadata     -> {meta_path}")
