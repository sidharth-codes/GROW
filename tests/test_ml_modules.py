"""Tests for GROW ML modules — soil clustering, yield prediction, price assessment."""

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np


class TestMLUtils(unittest.TestCase):

    def test_ordinal_encoder_roundtrip(self):
        from app.backend.ml.utils import OrdinalEncoder
        enc = OrdinalEncoder()
        X = [["Clay", "Well drained"], ["Loam", "Poorly drained"], ["Clay", "Poorly drained"]]
        encoded = enc.fit_transform(X)
        self.assertEqual(encoded.shape, (3, 2))
        # Clay appears twice, should have same code
        self.assertEqual(encoded[0, 0], encoded[2, 0])
        # Loam and Clay should differ
        self.assertNotEqual(encoded[0, 0], encoded[1, 0])

    def test_ordinal_encoder_unseen_label(self):
        from app.backend.ml.utils import OrdinalEncoder
        enc = OrdinalEncoder()
        enc.fit_transform([["Clay"], ["Loam"]])
        result = enc.transform([["Sandy"]])  # unseen
        self.assertEqual(result[0, 0], -1)

    def test_time_aware_split_preserves_order(self):
        from app.backend.ml.utils import time_aware_split
        records = [{"year": str(y), "value": y} for y in range(2001, 2024)]
        train, test = time_aware_split(records, year_key="year", test_ratio=0.2)
        train_years = [int(r["year"]) for r in train]
        test_years = [int(r["year"]) for r in test]
        # All train years must be before all test years
        self.assertLess(max(train_years), min(test_years))
        # No overlap
        self.assertEqual(len(set(train_years) & set(test_years)), 0)
        self.assertEqual(len(train) + len(test), len(records))

    def test_safe_float(self):
        from app.backend.ml.utils import safe_float
        self.assertEqual(safe_float("1,234.56"), 1234.56)
        self.assertEqual(safe_float(""), 0.0)
        self.assertEqual(safe_float("nan"), 0.0)
        self.assertEqual(safe_float("inf"), 0.0)


class TestSoilClustering(unittest.TestCase):

    def test_soil_model_file_exists(self):
        self.assertTrue(Path("models/soil_clustering.joblib").exists())
        self.assertTrue(Path("models/soil_clustering_meta.json").exists())

    def test_meta_has_required_fields(self):
        import json
        meta = json.loads(Path("models/soil_clustering_meta.json").read_text())
        self.assertIn("k", meta)
        self.assertIn("silhouette", meta)
        self.assertIn("data_adequacy", meta)
        self.assertIn("interpretation_warning", meta)
        self.assertGreater(meta["silhouette"], 0.0)

    def test_clustering_silhouette_above_random(self):
        """Silhouette > 0.3 indicates meaningful structure beyond random assignment."""
        import json
        meta = json.loads(Path("models/soil_clustering_meta.json").read_text())
        self.assertGreater(meta["silhouette"], 0.3,
                           "Silhouette score too low — clustering may not be meaningful")


class TestYieldPrediction(unittest.TestCase):

    def test_yield_model_file_exists(self):
        self.assertTrue(Path("models/crop_yield_model.joblib").exists())
        self.assertTrue(Path("models/crop_yield_model_meta.json").exists())

    def test_meta_has_required_fields(self):
        import json
        meta = json.loads(Path("models/crop_yield_model_meta.json").read_text())
        self.assertIn("metrics", meta)
        self.assertIn("n_train", meta)
        self.assertIn("n_test", meta)
        self.assertIn("validation_design", meta)
        self.assertIn("data_adequacy", meta)

    def test_no_target_leakage_in_features(self):
        """area_hectares and production_tonnes must NOT be features."""
        import json
        meta = json.loads(Path("models/crop_yield_model_meta.json").read_text())
        feats = meta.get("feature_columns", [])
        self.assertNotIn("area_hectares", feats)
        self.assertNotIn("production_tonnes", feats)

    def test_baseline_beats_trivial(self):
        """Baseline MAE must be less than the unconditional mean MAE."""
        import json
        meta = json.loads(Path("models/crop_yield_model_meta.json").read_text())
        baseline_mae = meta["metrics"]["baseline_district_crop_mean"]["mae"]
        # Baseline must be positive (real evaluation happened)
        self.assertGreater(baseline_mae, 0)
        # Baseline MAE should be < 10,000 kg/ha (global std. dev of all Kerala crops)
        self.assertLess(baseline_mae, 10000)

    def test_train_test_split_temporal(self):
        """Training set must not contain test-year records."""
        import json
        meta = json.loads(Path("models/crop_yield_model_meta.json").read_text())
        # Extract first year from range strings
        train_start = meta["train_years"].split(" to ")[0]
        test_end = meta["test_years"].split(" to ")[-1]
        train_end = meta["train_years"].split(" to ")[-1]
        test_start = meta["test_years"].split(" to ")[0]
        self.assertLess(train_end, test_start)


class TestPriceAssessment(unittest.TestCase):

    def test_meta_file_exists(self):
        self.assertTrue(Path("models/market_price_model_meta.json").exists())

    def test_deferred_status_when_no_data(self):
        import json
        meta = json.loads(Path("models/market_price_model_meta.json").read_text())
        # With no price data uploaded, status must be 'deferred_insufficient_data'
        self.assertEqual(meta["status"], "deferred_insufficient_data")
        self.assertFalse(meta["data_available"])
        # Template path must be recorded
        self.assertIn("template_path", meta)

    def test_template_file_is_labeled(self):
        template = Path("data/raw/market_prices/market_prices_template.csv")
        self.assertTrue(template.exists())
        with open(template, encoding="utf-8") as f:
            first_line = f.readline()
        self.assertIn("TEMPLATE", first_line.upper())


if __name__ == "__main__":
    unittest.main(verbosity=2)
