"""Unit tests for Crop Yield and Market Price ingestion pipelines."""

import json
import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.backend.yield_ingestion.processor import CropYieldProcessor
from app.backend.price_ingestion.normalizer import MarketPriceNormalizer
from app.backend.price_ingestion.fetcher import AgmarknetPriceFetcher
from app.backend.price_ingestion.pipeline import MarketPriceIngestionPipeline
from app.backend.dataset_manager.validator import DatasetValidator
from app.backend.dataset_manager.schemas import ValidationResult


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

    def test_provider_kerala_state_and_district_aliases_normalize_canonically(self):
        record = self.price_normalizer.normalize_record(
            self._api_record(state="Keralam", district="Thirssur")
        )
        self.assertIsNotNone(record)
        self.assertEqual(record["district"], "Thrissur")
        palakkad_record = self.price_normalizer.normalize_record(
            self._api_record(state="Keralam", district="Palakad")
        )
        self.assertIsNotNone(palakkad_record)
        self.assertEqual(palakkad_record["district"], "Palakkad")

    def test_provider_without_unit_preserves_values_as_unverified(self):
        source = self._api_record(state="Keralam")
        source.pop("price_unit")

        record = self.price_normalizer.normalize_record(source)

        self.assertIsNotNone(record)
        self.assertEqual(record["min_price"], 20.0)
        self.assertEqual(record["max_price"], 30.0)
        self.assertEqual(record["modal_price"], 25.0)
        self.assertEqual(record["price_unit"], "UNVERIFIED_SOURCE_UNIT")

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

    def _make_price_pipeline(self):
        temp_dir = tempfile.TemporaryDirectory()
        pipeline = MarketPriceIngestionPipeline(base_data_dir=temp_dir.name)
        return temp_dir, pipeline

    def _write_existing_price_files(self, data_dir):
        content = (
            "date,district,market,crop,variety,min_price,max_price,modal_price,price_unit,source\n"
            "2023-05-12,Palakkad,Old Market,Rice,Common,100,120,110,INR/quintal,VERIFIED\n"
        )
        targets = [
            Path(data_dir) / "market_prices.csv",
            Path(data_dir) / "processed" / "market_prices.csv",
        ]
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return {target: target.read_bytes() for target in targets}

    def _api_record(self, **overrides):
        record = {
            "state": "Kerala",
            "district": "Palakkad",
            "market": "  Palakkad   Market ",
            "commodity": "Paddy(Dhan)(Common)",
            "variety": "Jyothi",
            "arrival_date": "12/05/2023",
            "min_price": "20",
            "max_price": "30",
            "modal_price": "25",
            "price_unit": "Rs./Kg",
        }
        record.update(overrides)
        return record

    def test_pipeline_parses_documented_provider_json_and_normalizes_records(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        response = Mock(
            status_code=200,
            text=json.dumps({
                "status": "ok",
                "title": pipeline.fetcher.RESOURCE_TITLE,
                "total": 1,
                "count": 1,
                "offset": 0,
                "records": [self._api_record()],
            }),
        )

        with patch(
            "app.backend.price_ingestion.fetcher.requests.get",
            return_value=response,
        ):
            result = pipeline.run(api_key="test-key")

        self.assertTrue(result["success"])
        self.assertEqual(result["total_records"], 1)
        with open(result["processed_file"], newline="", encoding="utf-8") as f:
            saved = next(csv.DictReader(f))
        self.assertEqual(saved["date"], "2023-05-12")
        self.assertEqual(saved["district"], "Palakkad")
        self.assertEqual(saved["market"], "Palakkad Market")
        self.assertEqual(saved["crop"], "Rice")
        self.assertEqual(saved["min_price"], "2000.0")
        self.assertEqual(saved["modal_price"], "2500.0")
        self.assertEqual(saved["price_unit"], "INR/quintal")

    def test_unverified_provider_unit_migrates_existing_same_source_record(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)
        for path in original:
            content = path.read_text(encoding="utf-8")
            path.write_text(
                content.replace(
                    "2023-05-12,Palakkad,Old Market,Rice,Common,100,120,110,INR/quintal,VERIFIED",
                    "2023-05-12,Palakkad,Old Market,Rice,Common,100,120,110,INR/quintal,DATA.GOV.IN_AGMARKNET_API",
                ),
                encoding="utf-8",
            )
        source = self._api_record(
            state="Keralam",
            district="Palakkad",
            market="Old Market",
            crop="Rice",
            date="2023-05-12",
            arrival_date="12/05/2023",
            min_price="100",
            max_price="120",
            modal_price="110",
        )
        source.pop("price_unit")
        json_file = Path(temp_dir.name) / "unit_unverified.json"
        json_file.write_text(json.dumps({"records": [source]}), encoding="utf-8")

        result = pipeline.run(input_file_path=str(json_file))

        self.assertTrue(result["success"])
        self.assertEqual(result["imported_records"], 0)
        self.assertEqual(result["records_updated"], 1)
        with open(result["processed_file"], newline="", encoding="utf-8") as stream:
            saved = next(csv.DictReader(stream))
        self.assertEqual(saved["price_unit"], "UNVERIFIED_SOURCE_UNIT")

    def test_fetcher_uses_keralam_and_rejects_kerala_filter_no_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = AgmarknetPriceFetcher(raw_dir=temp_dir)

            def response_for_filter(_url, params, timeout):
                self.assertEqual(timeout, 20)
                rows = [self._api_record(state="Keralam")] if params["filters[state]"] == "Keralam" else []
                return Mock(
                    status_code=200,
                    text=json.dumps({
                        "status": "ok",
                        "title": fetcher.RESOURCE_TITLE,
                        "total": len(rows),
                        "count": len(rows),
                        "offset": params["offset"],
                        "records": rows,
                    }),
                )

            with patch(
                "app.backend.price_ingestion.fetcher.requests.get",
                side_effect=response_for_filter,
            ) as get:
                success, raw_path, _ = fetcher.attempt_api_download("test-key")
                self.assertTrue(success)
                self.assertEqual(get.call_args.kwargs["params"]["filters[state]"], "Keralam")
                self.assertTrue(raw_path.exists())
                raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
                self.assertEqual(raw_payload["records"][0]["state"], "Keralam")
                self.assertEqual(
                    raw_payload["_provenance"]["price_unit_status"], "unverified"
                )
                self.assertIsNone(
                    raw_payload["_provenance"]["normalized_price_unit"]
                )
                self.assertNotIn("api-key", json.dumps(raw_payload))

                with patch.object(AgmarknetPriceFetcher, "STATE_FILTER", "Kerala"):
                    success, failed_path, message = fetcher.attempt_api_download("test-key")

            self.assertFalse(success)
            self.assertIsNone(failed_path)
            self.assertIn("no market-price records", message)

    def test_fetcher_paginates_using_offset_and_preserves_response_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = AgmarknetPriceFetcher(raw_dir=temp_dir)
            fetcher.PAGE_SIZE = 2
            rows = [
                self._api_record(arrival_date="10/05/2023", market="Market A"),
                self._api_record(arrival_date="11/05/2023", market="Market B"),
                self._api_record(arrival_date="12/05/2023", market="Market C"),
            ]

            def paged_response(_url, params, timeout):
                offset = params["offset"]
                page = rows[offset:offset + params["limit"]]
                return Mock(
                    status_code=200,
                    text=json.dumps({
                        "status": "ok",
                        "title": fetcher.RESOURCE_TITLE,
                        "total": len(rows),
                        "count": len(page),
                        "offset": offset,
                        "records": page,
                    }),
                )

            with patch(
                "app.backend.price_ingestion.fetcher.requests.get",
                side_effect=paged_response,
            ) as get:
                success, raw_path, _ = fetcher.attempt_api_download("test-key")

            self.assertTrue(success)
            self.assertEqual([call.kwargs["params"]["offset"] for call in get.call_args_list], [0, 2])
            saved = json.loads(raw_path.read_text(encoding="utf-8"))
            self.assertEqual(len(saved["_raw_responses"]), 2)
            self.assertEqual(saved["_provenance"]["retrieved_count"], 3)
            self.assertEqual(saved["_provenance"]["page_count"], 2)

    def test_pipeline_rejects_malformed_price_records_without_replacing_data(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)
        invalid_records = [
            self._api_record(arrival_date="31/02/2023"),
            self._api_record(commodity=" "),
            self._api_record(market=" "),
            self._api_record(min_price="not-a-price"),
            self._api_record(min_price="-1"),
            self._api_record(min_price="40", max_price="30", modal_price="35"),
            self._api_record(min_price="20", max_price="30", modal_price="35"),
        ]
        json_file = Path(temp_dir.name) / "invalid_records.json"
        json_file.write_text(json.dumps({"records": invalid_records}), encoding="utf-8")

        result = pipeline.run(input_file_path=str(json_file))

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "normalization_failed")
        self.assertEqual(result["records_retrieved"], len(invalid_records))
        self.assertEqual(result["rejected_records"], len(invalid_records))
        for path, contents in original.items():
            self.assertEqual(path.read_bytes(), contents)

    def test_pipeline_import_is_idempotent_and_removes_duplicate_keys(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        duplicate = self._api_record(state="Keralam")
        json_file = Path(temp_dir.name) / "duplicates.json"
        json_file.write_text(
            json.dumps({"records": [duplicate, duplicate]}),
            encoding="utf-8",
        )

        first_result = pipeline.run(input_file_path=str(json_file))
        self.assertTrue(first_result["success"])
        self.assertEqual(first_result["valid_records"], 2)
        self.assertEqual(first_result["imported_records"], 1)
        self.assertEqual(first_result["duplicates_removed"], 1)
        original_root = (Path(temp_dir.name) / "market_prices.csv").read_bytes()
        original_processed = (
            Path(temp_dir.name) / "processed" / "market_prices.csv"
        ).read_bytes()

        second_result = pipeline.run(input_file_path=str(json_file))

        self.assertTrue(second_result["success"])
        self.assertEqual(second_result["imported_records"], 0)
        self.assertEqual(second_result["duplicates_removed"], 2)
        self.assertEqual(second_result["input_duplicates_removed"], 1)
        self.assertEqual(second_result["existing_record_matches"], 1)
        self.assertEqual((Path(temp_dir.name) / "market_prices.csv").read_bytes(), original_root)
        self.assertEqual(
            (Path(temp_dir.name) / "processed" / "market_prices.csv").read_bytes(),
            original_processed,
        )
        with open(second_result["processed_file"], newline="", encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 1)

    def test_pipeline_reads_data_gov_api_key_from_environment(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        with patch.dict(os.environ, {"DATA_GOV_IN_API_KEY": "test-key"}):
            with patch.object(
                pipeline.fetcher,
                "attempt_api_download",
                return_value=(False, None, "provider rejected request"),
            ) as attempt:
                result = pipeline.run()

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "download_failed")
        attempt.assert_called_once_with(api_key="test-key")

    def test_empty_provider_json_does_not_replace_existing_dataset(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)
        json_file = Path(temp_dir.name) / "empty.json"
        json_file.write_text('{"records": []}', encoding="utf-8")

        result = pipeline.run(input_file_path=str(json_file))

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "parse_failed")
        for path, contents in original.items():
            self.assertEqual(path.read_bytes(), contents)

    def test_malformed_json_does_not_replace_existing_dataset(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)
        json_file = Path(temp_dir.name) / "malformed.json"
        json_file.write_text('{"records": [', encoding="utf-8")

        result = pipeline.run(input_file_path=str(json_file))

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "parse_failed")
        for path, contents in original.items():
            self.assertEqual(path.read_bytes(), contents)

    def test_missing_json_fields_do_not_replace_existing_dataset(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)
        json_file = Path(temp_dir.name) / "missing_fields.json"
        json_file.write_text(
            json.dumps({"records": [self._api_record(modal_price=None)]}),
            encoding="utf-8",
        )

        result = pipeline.run(input_file_path=str(json_file))

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "normalization_failed")
        for path, contents in original.items():
            self.assertEqual(path.read_bytes(), contents)

    def test_schema_validation_failure_does_not_replace_existing_dataset(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)
        csv_file = Path(temp_dir.name) / "valid_input.csv"
        csv_file.write_text(
            "date,district,market,crop,min_price,max_price,modal_price,price_unit\n"
            "12/05/2023,Palakkad,Market,Paddy,20,30,25,Rs./Kg\n",
            encoding="utf-8",
        )
        pipeline.validator.validate_file = Mock(return_value=ValidationResult(
            is_valid=False,
            record_count=1,
            column_count=10,
            missing_value_count=0,
            missing_values_by_column={},
            duplicate_record_count=0,
            errors=["validation failure"],
            warnings=[],
        ))

        result = pipeline.run(input_file_path=str(csv_file))

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "validation_failed")
        for path, contents in original.items():
            self.assertEqual(path.read_bytes(), contents)
        self.assertEqual(
            list((Path(temp_dir.name) / "processed").glob(".market_prices.*.csv")),
            [],
        )

    def test_provider_error_does_not_replace_existing_dataset(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)
        pipeline.fetcher.attempt_api_download = Mock(
            return_value=(False, None, "Data.gov.in API error: invalid API key")
        )

        result = pipeline.run(api_key="not-a-real-key")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "download_failed")
        self.assertIn("invalid API key", result["error"])
        for path, contents in original.items():
            self.assertEqual(path.read_bytes(), contents)

    def test_provider_fetcher_rejects_error_json_and_preserves_prior_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = AgmarknetPriceFetcher(raw_dir=temp_dir)
            raw_path = Path(temp_dir) / "data_gov_in_kerala_prices.json"
            raw_path.write_text('{"records": [{"old": true}]}', encoding="utf-8")
            response = Mock(status_code=200, text='{"error":"invalid API key"}')

            with patch(
                "app.backend.price_ingestion.fetcher.requests.get",
                return_value=response,
            ):
                success, result_path, message = fetcher.attempt_api_download("fake-api-token")

            self.assertFalse(success)
            self.assertIsNone(result_path)
            self.assertIn("invalid API key", message)
            self.assertEqual(
                raw_path.read_text(encoding="utf-8"),
                '{"records": [{"old": true}]}',
            )

    def test_template_sample_prices_are_not_ingested_as_observations(self):
        temp_dir, pipeline = self._make_price_pipeline()
        self.addCleanup(temp_dir.cleanup)
        original = self._write_existing_price_files(temp_dir.name)

        result = pipeline.run(input_file_path=str(pipeline.fetcher.template_file))

        self.assertFalse(result["success"])
        self.assertIn("Template files", result["error"])
        for path, contents in original.items():
            self.assertEqual(path.read_bytes(), contents)


if __name__ == "__main__":
    unittest.main()
