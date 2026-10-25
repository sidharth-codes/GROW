"""Comprehensive tests for GROW Dataset Management Module.

Tests schema verification, validation rules, error handling, manual upload
guidance, and safe staging without pandas dependency.
"""

import csv
import json
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
            "market_prices", "cultivation_cost", "cultivation_cost_summary",
            "cultivation_cost_a", "demand",
            "market_arrivals", "crop_calendar", "soil_crop_suitability_v2"
        ]
        for domain in expected_domains:
            self.assertIn(domain, DATASET_SCHEMAS)
            schema = DATASET_SCHEMAS[domain]
            self.assertGreater(len(schema["columns"]), 0)
            self.assertIsNotNone(schema["source_info"].organization)
            self.assertIsNotNone(schema["source_info"].source_url)
            self.assertIsNotNone(schema["source_info"].expected_filename)

    def test_existing_registry_is_extended_with_new_schemas(self):
        legacy_dir = os.path.join(self.temp_dir, "legacy_metadata")
        os.makedirs(legacy_dir)
        legacy_registry_file = os.path.join(legacy_dir, "legacy_registry.json")
        with open(legacy_registry_file, "w", encoding="utf-8") as f:
            f.write('{"existing_dataset": {"status": "available"}}')

        upgraded = DatasetRegistry(
            metadata_dir=legacy_dir,
            registry_filename="legacy_registry.json",
            validator=self.validator,
        )

        self.assertEqual(upgraded.get("existing_dataset")["status"], "available")
        self.assertEqual(
            upgraded.get("cultivation_cost_summary")["geographic_resolution"],
            "State",
        )

    def test_cost_summary_schema_preserves_missing_reported_values(self):
        cost_summary = os.path.join(self.temp_dir, "cost_summary.csv")
        with open(cost_summary, "w", encoding="utf-8") as f:
            f.write(
                "agriculture_year,crop,season,reported_input_cost_rs_per_ha,"
                "reported_value_of_output_rs_per_ha,currency,area_unit,"
                "source_table_label,source_url,source_status,notes\n"
            )
            f.write(
                "2022-23,Beans,Summer,,,INR,hectare,Summary table,"
                "https://example.org/report,transcribed,Source values unavailable\n"
            )

        result = self.validator.validate_file(cost_summary, "cultivation_cost_summary")

        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.record_count, 1)
        self.assertEqual(result.missing_value_count, 2)
        self.assertEqual(result.missing_values_by_column["reported_input_cost_rs_per_ha"], 1)
        self.assertEqual(result.missing_values_by_column["reported_value_of_output_rs_per_ha"], 1)
        self.assertEqual(
            self.registry.get("cultivation_cost_summary")["geographic_resolution"],
            "State",
        )

    def test_enrichment_pack_cost_summary_validates(self):
        result = self.validator.validate_file(
            "data/kerala_cost_of_cultivation_summary_2022_23_2023_24.csv",
            "cultivation_cost_summary",
        )
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.record_count, 70)
        self.assertEqual(result.missing_value_count, 2)

    def test_official_cost_summary_verification_is_recorded(self):
        metadata_path = Path("data/metadata/kerala_cost_summary_verification.json")
        verification = json.loads(metadata_path.read_text(encoding="utf-8"))
        result = self.validator.validate_file(
            "data/processed/kerala_cost_of_cultivation_summary_2022_23_2023_24.csv",
            "cultivation_cost_summary",
        )

        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.record_count, 70)
        self.assertEqual(result.missing_value_count, 2)
        self.assertEqual(verification["numeric_rows_verified"], 69)
        self.assertEqual(verification["mismatches"], 0)
        self.assertEqual(
            verification["periods"]["2022-23"]["matched_numeric_rows"],
            34,
        )
        self.assertEqual(
            verification["periods"]["2023-24"]["matched_numeric_rows"],
            35,
        )
        self.assertEqual(verification["periods"]["2022-23"]["unreported_rows"], 1)

    def test_verified_cost_a_series_validates_and_preserves_reported_zeros(self):
        path = (
            "data/processed/kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv"
        )
        result = self.validator.validate_file(path, "cultivation_cost_a")

        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.record_count, 350)
        self.assertEqual(result.duplicate_record_count, 0)
        self.assertEqual(result.missing_value_count, 0)
        with open(path, encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(
            sum(float(row["cost_a_rs_per_hectare"]) == 0 for row in rows),
            108,
        )
        self.assertEqual(
            {row["cost_year"] for row in rows},
            {
                "2014-15", "2015-16", "2016-17", "2017-18", "2018-19",
                "2019-20", "2020-21", "2021-22", "2022-23", "2023-24",
            },
        )

    def test_cost_a_series_is_verified_and_registered_separately(self):
        reference_path = Path(
            "data/reference/kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv"
        )
        with reference_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)

        self.assertEqual(
            reader.fieldnames,
            ["crop_season", "cost_year", "cost_a_rs_per_hectare", "state", "source", "notes"],
        )
        self.assertEqual(len(rows), 350)
        self.assertEqual(
            {row["cost_year"] for row in rows},
            {
                "2014-15", "2015-16", "2016-17", "2017-18", "2018-19",
                "2019-20", "2020-21", "2021-22", "2022-23", "2023-24",
            },
        )
        self.assertEqual(
            sum(row["cost_a_rs_per_hectare"] == "0" for row in rows),
            108,
        )
        self.assertNotIn("cost_a_reference", DATASET_SCHEMAS)
        canonical_path = Path(
            "data/processed/kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv"
        )
        canonical_validation = self.validator.validate_file(
            str(canonical_path), "cultivation_cost_a"
        )
        self.assertTrue(canonical_validation.is_valid, canonical_validation.errors)
        self.assertEqual(canonical_validation.record_count, 350)
        self.registry.sync_with_existing_files("data")
        self.assertEqual(
            self.registry.get("cultivation_cost_a")["status"],
            "partially_available",
        )

    def test_missing_data_pack_templates_are_header_only(self):
        template_dir = Path("data/templates/missing_data_pack")
        templates = sorted(template_dir.glob("*.csv"))

        self.assertEqual(len(templates), 9)
        for template in templates:
            with self.subTest(template=template.name):
                with template.open(encoding="utf-8-sig", newline="") as stream:
                    reader = csv.reader(stream)
                    self.assertTrue(next(reader, []), f"{template} must define columns")
                    self.assertEqual(list(reader), [], f"{template} must not contain observations")

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
        empty_csv = os.path.join(self.temp_dir, "empty_file.csv")
        with open(empty_csv, "w", encoding="utf-8") as f:
            pass  # 0 bytes
        res = self.validator.validate_file(empty_csv, "crop_yield")
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
        self.assertEqual(res.record_count, 60329)
        self.assertEqual(res.column_count, 9)
        self.assertEqual(res.missing_value_count, 0)
        self.assertEqual(res.duplicate_record_count, 0)

    def test_validate_malformed_csv(self):
        """Malformed CSV with missing required columns and bad types."""
        bad_csv = os.path.join(self.temp_dir, "bad_crops.csv")
        with open(bad_csv, "w", encoding="utf-8") as f:
            f.write("crop,preferred_soil_texture\n")
            f.write("Wheat,Loam\n")

        res = self.validator.validate_file(bad_csv, "crops")
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Missing required columns" in e for e in res.errors))
        self.assertTrue(any(bad_csv in e for e in res.errors))
        self.assertTrue(any("preferred_drainage" in e for e in res.errors))

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

    def test_duplicate_primary_key_is_an_error_with_location(self):
        dup_csv = os.path.join(self.temp_dir, "duplicate_crops.csv")
        with open(dup_csv, "w", encoding="utf-8") as f:
            f.write("crop,preferred_soil_texture,preferred_drainage,preferred_ph_range,water_requirement,growing_season\n")
            f.write("Rice,Clay,Poorly drained,5.0-6.5,High,Monsoon\n")
            f.write("Rice,Clay,Poorly drained,5.0-6.5,High,Monsoon\n")

        res = self.validator.validate_file(dup_csv, "crops")

        self.assertFalse(res.is_valid)
        self.assertEqual(res.duplicate_record_count, 1)
        self.assertTrue(any(
            dup_csv in error and "row 3" in error and "column 'crop'" in error
            for error in res.errors
        ))

    def test_non_finite_float_values_are_rejected_with_location(self):
        non_finite_csv = os.path.join(self.temp_dir, "non_finite_weather.csv")
        with open(non_finite_csv, "w", encoding="utf-8") as f:
            f.write("district,date,rainfall_mm,temperature_min_c,temperature_max_c,humidity_percent,latitude,longitude,source\n")
            for day, value in enumerate(("NaN", "inf", "-inf"), start=1):
                f.write(f"Palakkad,2024-01-{day:02d},{value},20,30,60,10,76,NASA\n")

        res = self.validator.validate_file(non_finite_csv, "weather")

        self.assertFalse(res.is_valid)
        for row in range(2, 5):
            self.assertTrue(any(
                non_finite_csv in error
                and f"row {row}" in error
                and "column 'rainfall_mm'" in error
                and "finite" in error
                for error in res.errors
            ))

    def test_non_finite_integer_values_are_rejected(self):
        non_finite_csv = os.path.join(self.temp_dir, "non_finite_calendar.csv")
        with open(non_finite_csv, "w", encoding="utf-8") as f:
            f.write("district,crop,season,sowing_start_month,sowing_end_month,harvest_start_month,harvest_end_month,duration_days,source\n")
            for day, value in enumerate(("NaN", "inf", "-inf"), start=1):
                f.write(
                    f"Palakkad,Rice,Season {day},1,8,9,11,{value},KAU\n"
                )

        res = self.validator.validate_file(non_finite_csv, "crop_calendar")

        self.assertFalse(res.is_valid)
        for row in range(2, 5):
            self.assertTrue(any(
                non_finite_csv in error
                and f"row {row}" in error
                and "column 'duration_days'" in error
                and "finite" in error
                for error in res.errors
            ))

    def test_fractional_integer_value_is_rejected(self):
        calendar_csv = os.path.join(self.temp_dir, "fractional_calendar.csv")
        with open(calendar_csv, "w", encoding="utf-8") as f:
            f.write("district,crop,season,sowing_start_month,sowing_end_month,harvest_start_month,harvest_end_month,duration_days,source\n")
            f.write("Palakkad,Rice,Monsoon,1.5,8,9,11,120,KAU\n")

        res = self.validator.validate_file(calendar_csv, "crop_calendar")

        self.assertFalse(res.is_valid)
        self.assertTrue(any(
            calendar_csv in error
            and "row 2" in error
            and "column 'sowing_start_month'" in error
            and "fractional" in error
            for error in res.errors
        ))

    def test_invalid_row_is_rejected_even_when_file_has_warnings(self):
        crops_csv = os.path.join(self.temp_dir, "warning_and_invalid_row.csv")
        with open(crops_csv, "w", encoding="utf-8") as f:
            f.write("crop,preferred_soil_texture,preferred_drainage,preferred_ph_range,water_requirement,growing_season,notes\n")
            f.write("Rice,Clay,Poorly drained,unknown,High,Monsoon,extra metadata\n")

        res = self.validator.validate_file(crops_csv, "crops")

        self.assertFalse(res.is_valid)
        self.assertTrue(res.warnings)
        self.assertTrue(any(
            crops_csv in error
            and "row 2" in error
            and "column 'preferred_ph_range'" in error
            for error in res.errors
        ))

    def test_required_value_and_numeric_type_errors_include_location(self):
        missing_value_csv = os.path.join(self.temp_dir, "missing_crop.csv")
        with open(missing_value_csv, "w", encoding="utf-8") as f:
            f.write("crop,preferred_soil_texture,preferred_drainage,preferred_ph_range,water_requirement,growing_season\n")
            f.write(",Clay,Poorly drained,5.0-6.5,High,Monsoon\n")

        missing_value_result = self.validator.validate_file(missing_value_csv, "crops")
        self.assertFalse(missing_value_result.is_valid)
        self.assertTrue(any(
            missing_value_csv in error
            and "row 2" in error
            and "column 'crop'" in error
            and "Missing required value" in error
            for error in missing_value_result.errors
        ))

        invalid_type_csv = os.path.join(self.temp_dir, "invalid_weather_type.csv")
        with open(invalid_type_csv, "w", encoding="utf-8") as f:
            f.write("district,date,rainfall_mm,temperature_min_c,temperature_max_c,humidity_percent,latitude,longitude,source\n")
            f.write("Palakkad,2024-01-01,wet,20,30,60,10,76,NASA\n")

        invalid_type_result = self.validator.validate_file(invalid_type_csv, "weather")
        self.assertFalse(invalid_type_result.is_valid)
        self.assertTrue(any(
            invalid_type_csv in error
            and "row 2" in error
            and "column 'rainfall_mm'" in error
            and "Cannot parse" in error
            for error in invalid_type_result.errors
        ))

    def test_malformed_row_width_reports_file_row_and_column(self):
        malformed_csv = os.path.join(self.temp_dir, "malformed_row_width.csv")
        with open(malformed_csv, "w", encoding="utf-8") as f:
            f.write("district,date,rainfall_mm,temperature_min_c,temperature_max_c,humidity_percent,latitude,longitude,source\n")
            f.write("Palakkad,2024-01-01,10,20,30,60,10,76\n")
            f.write("Palakkad,2024-01-02,10,20,30,60,10,76,NASA,unexpected\n")

        res = self.validator.validate_file(malformed_csv, "weather")

        self.assertFalse(res.is_valid)
        self.assertTrue(any(
            malformed_csv in error
            and "row 2" in error
            and "column 'source'" in error
            for error in res.errors
        ))
        self.assertTrue(any(
            malformed_csv in error
            and "row 3" in error
            and "column 'extra_fields'" in error
            for error in res.errors
        ))

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

    def test_cost_summary_upload_remains_partially_available(self):
        summary_csv = os.path.join(self.temp_dir, "state_cost_summary.csv")
        with open(summary_csv, "w", encoding="utf-8") as f:
            f.write(
                "agriculture_year,crop,season,reported_input_cost_rs_per_ha,"
                "reported_value_of_output_rs_per_ha,currency,area_unit,"
                "source_table_label,source_url,source_status,notes\n"
            )
            f.write(
                "2023-24,Paddy,Autumn,82488,117719,INR,hectare,Summary table,"
                "https://example.org/report,transcribed,State-level test fixture\n"
            )

        result = self.service.commit_upload(
            summary_csv,
            "cultivation_cost_summary",
            "state_cost_summary.csv",
        )

        self.assertTrue(result["success"])
        self.assertEqual(
            self.registry.get("cultivation_cost_summary")["status"],
            "partially_available",
        )


if __name__ == "__main__":
    unittest.main()
