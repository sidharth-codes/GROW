"""Unit tests for Crop Yield and Market Price ingestion pipelines."""

import os
import unittest
from pathlib import Path

from app.backend.yield_ingestion.processor import CropYieldProcessor
from app.backend.price_ingestion.normalizer import MarketPriceNormalizer
from app.backend.price_ingestion.fetcher import AgmarknetPriceFetcher
from app.backend.dataset_manager.validator import DatasetValidator


class TestYieldAndPricePipelines(unittest.TestCase):

    def setUp(self):
        self.yield_processor = CropYieldProcessor()
        self.price_normalizer = MarketPriceNormalizer()
        self.validator = DatasetValidator()

    def test_crop_name_mapping(self):
        """Verify standard agricultural crop name normalization."""
        from app.backend.yield_ingestion.processor import CROP_NAME_MAPPING
        self.assertEqual(CROP_NAME_MAPPING["Paddy"], "Rice")
        self.assertEqual(CROP_NAME_MAPPING["Pepper"], "Black pepper")
        self.assertEqual(CROP_NAME_MAPPING["Tapioca"], "Tapioca")
        self.assertEqual(CROP_NAME_MAPPING["Rubber"], "Rubber")

    def test_price_date_parsing(self):
        """Test parsing of multiple real-world date formats into ISO YYYY-MM-DD."""
        norm = self.price_normalizer
        self.assertEqual(norm.parse_date("2023-05-12"), "2023-05-12")
        self.assertEqual(norm.parse_date("12/05/2023"), "2023-05-12")
        self.assertEqual(norm.parse_date("12-05-2023"), "2023-05-12")
        self.assertEqual(norm.parse_date("12-May-2023"), "2023-05-12")
        self.assertIsNone(norm.parse_date("invalid-date"))

    def test_price_unit_conversion(self):
        """Verify normalization to standard INR/quintal."""
        norm = self.price_normalizer
        # Rs. 35 per kg -> 3500 per quintal
        p, unit = norm.normalize_price_to_quintal(35.0, "Rs./Kg")
        self.assertEqual(p, 3500.0)
        self.assertEqual(unit, "INR/quintal")

        # Rs. 25000 per MT -> 2500 per quintal
        p, unit = norm.normalize_price_to_quintal(25000.0, "Rs./MT")
        self.assertEqual(p, 2500.0)

        # Standard quintal unchanged
        p, unit = norm.normalize_price_to_quintal(2150.0, "INR/quintal")
        self.assertEqual(p, 2150.0)

    def test_price_record_normalization(self):
        """Verify full market price record normalization."""
        norm = self.price_normalizer
        raw_row = {
            "date": "15/03/2023",
            "district": "Palakkad",
            "market": "Palakkad Mandi",
            "crop": "Paddy(Dhan)(Common)",
            "variety": "Jyothi",
            "min_price": "2100",
            "max_price": "2300",
            "modal_price": "2200",
            "price_unit": "INR/quintal",
        }
        res = norm.normalize_record(raw_row)
        self.assertIsNotNone(res)
        self.assertEqual(res["date"], "2023-03-15")
        self.assertEqual(res["district"], "Palakkad")
        self.assertEqual(res["crop"], "Rice")
        self.assertEqual(res["min_price"], 2100.0)
        self.assertEqual(res["modal_price"], 2200.0)
        self.assertEqual(res["max_price"], 2300.0)

    def test_real_crop_yield_dataset_validity(self):
        """Ensure the ingested crop yield dataset conforms to GROW schema."""
        yield_csv = "data/processed/crop_yield.csv"
        if os.path.exists(yield_csv):
            res = self.validator.validate_file(yield_csv, "crop_yield")
            self.assertTrue(res.is_valid)
            self.assertGreaterEqual(res.record_count, 6000)
            self.assertEqual(res.column_count, 8)
            self.assertEqual(res.missing_value_count, 0)

    def test_agmarknet_template_exists(self):
        """Ensure market prices template file is created and labeled."""
        fetcher = AgmarknetPriceFetcher()
        self.assertTrue(fetcher.template_file.exists())
        with open(fetcher.template_file, "r", encoding="utf-8") as f:
            first_line = f.readline()
            self.assertIn("TEMPLATE NOTICE", first_line)


if __name__ == "__main__":
    unittest.main()
