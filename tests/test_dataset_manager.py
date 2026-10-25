"""Comprehensive tests for GROW Dataset Management Module.

Tests schema verification, validation rules, error handling, manual upload
guidance, and safe staging without pandas dependency.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from app.backend.dataset_manager.schemas import DATASET_SCHEMAS, KERALA_DISTRICTS
from app.backend.dataset_manager.validator import DatasetValidator
from app.backend.dataset_manager.registry import DatasetRegistry
from app.backend.dataset_manager.ingestion import DatasetIngestionService


class TestDatasetManager(unittest.TestCase):

    def setUp(self):
        self.validator = DatasetValidator()
        self.temp_dir = tempfile.mkdtemp()
        self.metadata_dir = os.path.join(self.temp_dir, "metadata")
        self.registry = DatasetRegistry(
            metadata_dir=self.metadata_dir,
            registry_filename="test_registry.json",
            validator=self.validator
        )
        self.service = DatasetIngestionService(
            base_data_dir=self.temp_dir,
            registry=self.registry,
            validator=self.validator
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_coverage(self):
        """Verify all 9 agricultural dataset domains have defined schemas."""
        expected_domains = [
            "soil", "crops", "weather", "crop_yield",
            "market_prices", "cultivation_cost", "demand",
            "crop_calendar", "soil_crop_suitability_v2"
        ]
        for domain in expected_domains:
            self.assertIn(domain, DATASET_SCHEMAS)
            schema = DATASET_SCHEMAS[domain]
            self.assertGreater(len(schema["columns"]), 0)
            self.assertIsNotNone(schema["source_info"].organization)
            self.assertIsNotNone(schema["source_info"].source_url)
            self.assertIsNotNone(schema["source_info"].expected_filename)

    def test_validate_crops_real_file(self):
        """Validate existing data/crops.csv file."""
        res = self.validator.validate_file("data/crops.csv", "crops")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.record_count, 10)
        self.assertEqual(res.column_count, 6)
        self.assertEqual(res.missing_value_count, 0)
        self.assertEqual(len(res.errors), 0)

    def test_validate_soil_real_file(self):
        """Validate existing data/soil.csv file."""
        res = self.validator.validate_file("data/soil.csv", "soil")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.record_count, 23)
        self.assertEqual(res.column_count, 8)
        self.assertEqual(res.missing_value_count, 0)
        self.assertEqual(len(res.errors), 0)

    def test_validate_empty_file(self):
        """Empty files should fail validation with explicit error."""
        res = self.validator.validate_file("data/crop_yield.csv", "crop_yield")
        self.assertFalse(res.is_valid)
        self.assertEqual(res.record_count, 0)
        self.assertTrue(any("empty" in e.lower() for e in res.errors))

    def test_validate_header_only_weather_file(self):
        """Header-only files with 0 data rows should be marked invalid."""
        header_only_csv = os.path.join(self.temp_dir, "header_only_weather.csv")
        with open(header_only_csv, "w", encoding="utf-8") as f:
            f.write("district,date,rainfall_mm,temperature_min_c,temperature_max_c,humidity_percent,latitude,longitude,source\n")

        res = self.validator.validate_file(header_only_csv, "weather")
        self.assertFalse(res.is_valid)
        self.assertEqual(res.record_count, 0)
        self.assertTrue(any("0 data records" in e for e in res.errors))

    def test_validate_real_weather_file(self):
        """Validate the fully ingested real weather dataset."""
        res = self.validator.validate_file("data/weather.csv", "weather")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.record_count, 56252)
        self.assertEqual(res.column_count, 9)
        self.assertEqual(res.missing_value_count, 0)

    def test_validate_malformed_csv(self):
        """Malformed CSV with missing required columns and bad types."""
        bad_csv = os.path.join(self.temp_dir, "bad_crops.csv")
        with open(bad_csv, "w", encoding="utf-8") as f:
            f.write("crop,preferred_soil_texture\n")
            f.write("Wheat,Loam\n")

        res = self.validator.validate_file(bad_csv, "crops")
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Missing required columns" in e for e in res.errors))

    def test_validate_invalid_range_and_duplicate_keys(self):
        """Duplicate primary keys and invalid numeric ranges should be caught."""
        dup_csv = os.path.join(self.temp_dir, "dup_crops.csv")
        with open(dup_csv, "w", encoding="utf-8") as f:
            f.write("crop,preferred_soil_texture,preferred_drainage,preferred_ph_range,water_requirement,growing_season\n")
            f.write("Rice,Clay,Poorly drained,8.0-5.0,High,Monsoon\n")  # invalid range: 8 > 5
            f.write("Rice,Clay,Poorly drained,5.0-6.5,High,Monsoon\n")  # duplicate crop name

        res = self.validator.validate_file(dup_csv, "crops")
        self.assertFalse(res.is_valid)
        self.assertEqual(res.duplicate_record_count, 1)
        self.assertTrue(any("lower bound" in e for e in res.errors))

    def test_download_guidance(self):
        """Manual download guidance must provide official URLs and instructions."""
        guidance = self.service.get_manual_download_guidance("crop_yield")
        self.assertEqual(guidance["dataset_id"], "crop_yield")
        self.assertIn("ecostat.kerala.gov.in", guidance["official_portal_url"])
        self.assertIn("year", guidance["required_columns"])
        self.assertIn("yield_kg_per_hectare", guidance["required_columns"])
        self.assertIn("crop_yield.csv", guidance["expected_filename"])

    def test_upload_staging_and_commit(self):
        """Safe upload staging, SHA256 hashing, raw archiving, and registry update."""
        valid_csv = os.path.join(self.temp_dir, "new_crops.csv")
        with open(valid_csv, "w", encoding="utf-8") as f:
            f.write("crop,preferred_soil_texture,preferred_drainage,preferred_ph_range,water_requirement,growing_season\n")
            f.write("Cardamom,Loam,Well drained,5.5-6.5,High,Monsoon\n")

        # 1. Pre-staging inspection
        staged = self.service.inspect_and_stage_upload(valid_csv, "crops", "new_crops.csv")
        self.assertTrue(staged["accepted"])
        self.assertIsNotNone(staged["sha256"])
        self.assertEqual(len(staged["sample_rows"]), 1)

        # 2. Commit upload
        commit_res = self.service.commit_upload(valid_csv, "crops", "new_crops.csv", source_note="Test upload")
        self.assertTrue(commit_res["success"])
        self.assertEqual(commit_res["records_committed"], 1)
        self.assertTrue(os.path.exists(commit_res["raw_archive"]))
        self.assertTrue(os.path.exists(commit_res["processed_file"]))
        self.assertTrue(os.path.exists(commit_res["quality_report"]))

        # 3. Verify registry reflects updated status
        meta = self.registry.get("crops")
        self.assertEqual(meta["status"], "ready_for_analysis")
        self.assertEqual(meta["record_count"], 1)


if __name__ == "__main__":
    unittest.main()
