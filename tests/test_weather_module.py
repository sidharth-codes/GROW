"""Unit tests for the Weather Data Module."""

import tempfile
import unittest
from pathlib import Path

from app.backend.weather.coordinates import KERALA_DISTRICT_COORDINATES
from app.backend.weather.nasa_power import NasaPowerClient
from app.backend.weather.collector import WeatherCollector
from app.backend.dataset_manager.schemas import KERALA_DISTRICTS
from app.backend.dataset_manager.registry import DatasetRegistry
from app.backend.dataset_manager.validator import DatasetValidator


class TestWeatherModule(unittest.TestCase):

    def test_all_14_districts_represented(self):
        """Ensure all 14 Kerala administrative districts have representative coordinates."""
        for d in KERALA_DISTRICTS:
            self.assertIn(d, KERALA_DISTRICT_COORDINATES, f"District {d} missing from coordinates map")
            geo = KERALA_DISTRICT_COORDINATES[d]
            self.assertGreaterEqual(geo["latitude"], 8.0)
            self.assertLessEqual(geo["latitude"], 13.0)
            self.assertGreaterEqual(geo["longitude"], 74.5)
            self.assertLessEqual(geo["longitude"], 77.8)
            self.assertIn("elevation_m", geo)
            self.assertIn("region", geo)

    def test_parse_nasa_response_with_sentinels(self):
        """Verify that -999.0 missing sentinels are detected and filtered."""
        client = NasaPowerClient()
        mock_raw = {
            "properties": {
                "parameter": {
                    "PRECTOTCORR": {"20230101": 0.5, "20230102": -999.0, "20230103": 12.4},
                    "T2M_MIN": {"20230101": 21.0, "20230102": 20.5, "20230103": -999.0},
                    "T2M_MAX": {"20230101": 31.0, "20230102": 30.5, "20230103": 32.0},
                    "RH2M": {"20230101": 75.0, "20230102": 80.0, "20230103": 85.0},
                }
            }
        }
        records, meta = client._parse_nasa_response(
            mock_raw,
            district="Thiruvananthapuram",
            latitude=8.5241,
            longitude=76.9366
        )

        # 20230101 is complete, 20230102 has missing precip, 20230103 has missing Tmin
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["date"], "2023-01-01")
        self.assertEqual(records[0]["rainfall_mm"], 0.5)
        self.assertEqual(records[0]["temperature_min_c"], 21.0)
        self.assertEqual(records[0]["temperature_max_c"], 31.0)
        self.assertEqual(records[0]["humidity_percent"], 75.0)
        self.assertEqual(meta["missing_precipitation_days"], 1)
        self.assertEqual(meta["missing_tmin_days"], 1)

    def test_invalid_nasa_response_does_not_replace_raw_cache(self):
        class InvalidResponse:
            status_code = 200
            text = "invalid provider payload"

            def json(self):
                return {"unexpected": "shape"}

        class StubSession:
            def get(self, *args, **kwargs):
                return InvalidResponse()

        with tempfile.TemporaryDirectory() as temp_dir:
            client = NasaPowerClient(
                raw_storage_dir=temp_dir,
                max_retries=1,
                backoff_factor=0,
            )
            client.session = StubSession()
            cache_path = client.get_cache_path("Kollam", "20240101", "20240101")
            cache_path.write_text('{"previous":"valid raw cache"}', encoding="utf-8")

            success, records, metadata = client.fetch_district_daily(
                district="Kollam",
                latitude=8.89,
                longitude=76.61,
                start_date="20240101",
                end_date="20240101",
                force_refresh=True,
            )

            self.assertFalse(success)
            self.assertEqual(records, [])
            self.assertIn("no usable daily records", metadata["error"])
            self.assertEqual(
                cache_path.read_text(encoding="utf-8"),
                '{"previous":"valid raw cache"}',
            )

    def test_precipitation_outlier_is_preserved_for_validation(self):
        """The provider's precipitation value is not clamped by the parser."""
        client = NasaPowerClient()
        mock_raw = {
            "properties": {
                "parameter": {
                    "PRECTOTCORR": {"20230101": 1923.84},
                    "T2M_MIN": {"20230101": 21.0},
                    "T2M_MAX": {"20230101": 31.0},
                    "RH2M": {"20230101": 75.0},
                }
            },
            "header": {"time_standard": "LST", "api": {"version": "v2.10.1"}},
            "parameters": {
                "PRECTOTCORR": {"units": "mm/day"},
                "T2M_MIN": {"units": "C"},
                "T2M_MAX": {"units": "C"},
                "RH2M": {"units": "%"},
            },
        }
        records, metadata = client._parse_nasa_response(
            mock_raw,
            district="Kollam",
            latitude=8.8932,
            longitude=76.6141
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["rainfall_mm"], 1923.84)
        self.assertEqual(metadata["time_standard"], "LST")
        self.assertEqual(
            metadata["parameter_metadata"]["PRECTOTCORR"]["units"],
            "mm/day",
        )

    def test_weather_collector_promotes_only_valid_data(self):
        district = "Kollam"
        coordinates = KERALA_DISTRICT_COORDINATES[district]

        class StubClient:
            def fetch_district_daily(self, **kwargs):
                return True, [{
                    "district": district,
                    "date": "2024-01-01",
                    "rainfall_mm": 1.5,
                    "temperature_min_c": 20.0,
                    "temperature_max_c": 30.0,
                    "humidity_percent": 75.0,
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"],
                    "source": "NASA POWER",
                }], {"source_type": "local_raw_cache"}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            processed_dir = data_dir / "processed"
            processed_dir.mkdir(parents=True)
            existing_file = processed_dir / "weather.csv"
            existing_file.write_text(
                "district,date,rainfall_mm,temperature_min_c,temperature_max_c,"
                "humidity_percent,latitude,longitude,source\n"
                "Alappuzha,2023-01-01,2.0,21.0,31.0,70.0,9.4981,76.3388,NASA POWER\n",
                encoding="utf-8",
            )
            collector = WeatherCollector(
                base_data_dir=str(data_dir),
                client=StubClient(),
                registry=DatasetRegistry(metadata_dir=str(data_dir / "metadata")),
            )

            result = collector.run_ingestion(
                districts=[district],
                start_date="20240101",
                end_date="20240101",
                pause_between_calls=0,
            )

            self.assertTrue(result["success"], result.get("validation", {}).get("errors"))
            self.assertEqual(result["total_records"], 2)
            self.assertTrue(Path(result["processed_file"]).is_file())
            self.assertTrue((data_dir / "weather.csv").is_file())
            merged_contents = Path(result["processed_file"]).read_text(encoding="utf-8")
            self.assertIn("Alappuzha,2023-01-01", merged_contents)
            self.assertIn("Kollam,2024-01-01", merged_contents)
            validation = DatasetValidator().validate_file(result["processed_file"], "weather")
            self.assertTrue(validation.is_valid, validation.errors)

    def test_failed_weather_ingestion_preserves_existing_datasets(self):
        class FailedClient:
            def fetch_district_daily(self, **kwargs):
                return False, [], {"error": "provider unavailable"}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            processed_dir = data_dir / "processed"
            processed_dir.mkdir(parents=True)
            root_file = data_dir / "weather.csv"
            processed_file = processed_dir / "weather.csv"
            root_file.write_text("existing root data", encoding="utf-8")
            processed_file.write_text("existing processed data", encoding="utf-8")
            collector = WeatherCollector(
                base_data_dir=str(data_dir),
                client=FailedClient(),
                registry=DatasetRegistry(metadata_dir=str(data_dir / "metadata")),
            )

            result = collector.run_ingestion(
                districts=["Kollam"],
                start_date="20240101",
                end_date="20240101",
                pause_between_calls=0,
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "download_failed")
            self.assertEqual(root_file.read_text(encoding="utf-8"), "existing root data")
            self.assertEqual(processed_file.read_text(encoding="utf-8"), "existing processed data")

    def test_out_of_range_provider_precipitation_is_quarantined(self):
        district = "Kollam"
        coordinates = KERALA_DISTRICT_COORDINATES[district]
        existing_contents = (
            "district,date,rainfall_mm,temperature_min_c,temperature_max_c,"
            "humidity_percent,latitude,longitude,source\n"
            "Kollam,2025-01-01,1.5,20.0,30.0,75.0,8.8932,76.6141,NASA_POWER_AG_0.5DEG\n"
        )

        class OutOfRangeClient:
            def fetch_district_daily(self, **kwargs):
                common = {
                    "district": district,
                    "temperature_min_c": 20.0,
                    "temperature_max_c": 30.0,
                    "humidity_percent": 75.0,
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"],
                    "source": "NASA_POWER_AG_0.5DEG",
                }
                return True, [
                    {
                        **common,
                        "date": "2026-07-30",
                        "rainfall_mm": 20.0,
                    },
                    {
                        **common,
                        "date": "2026-07-31",
                        "rainfall_mm": 1269.36,
                    },
                ], {"source_type": "nasa_power_api"}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            processed_dir = data_dir / "processed"
            processed_dir.mkdir(parents=True)
            root_file = data_dir / "weather.csv"
            processed_file = processed_dir / "weather.csv"
            root_file.write_text(existing_contents, encoding="utf-8")
            processed_file.write_text(existing_contents, encoding="utf-8")
            collector = WeatherCollector(
                base_data_dir=str(data_dir),
                client=OutOfRangeClient(),
                registry=DatasetRegistry(metadata_dir=str(data_dir / "metadata")),
            )

            result = collector.run_ingestion(
                districts=[district],
                start_date="20260730",
                end_date="20260731",
                pause_between_calls=0,
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["total_records"], 2)
            self.assertEqual(result["rainfall_anomaly_count"], 1)
            self.assertTrue(Path(result["anomaly_file"]).is_file())
            anomaly_csv = Path(result["anomaly_file"]).read_text(encoding="utf-8")
            self.assertIn("1269.36", anomaly_csv)
            self.assertIn("schema maximum 1000.0", anomaly_csv)
            for target in (root_file, processed_file):
                updated = target.read_text(encoding="utf-8")
                self.assertIn("Kollam,2025-01-01", updated)
                self.assertIn("Kollam,2026-07-30", updated)
                self.assertNotIn("Kollam,2026-07-31", updated)

    def test_invalid_weather_response_preserves_existing_datasets(self):
        district = "Kollam"
        coordinates = KERALA_DISTRICT_COORDINATES[district]

        class InvalidClient:
            def fetch_district_daily(self, **kwargs):
                return True, [{
                    "district": district,
                    "date": "2024-01-01",
                    "rainfall_mm": float("nan"),
                    "temperature_min_c": 20.0,
                    "temperature_max_c": 30.0,
                    "humidity_percent": 75.0,
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"],
                    "source": "NASA POWER",
                }], {"source_type": "nasa_power_api"}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            processed_dir = data_dir / "processed"
            processed_dir.mkdir(parents=True)
            root_file = data_dir / "weather.csv"
            processed_file = processed_dir / "weather.csv"
            header = (
                "district,date,rainfall_mm,temperature_min_c,temperature_max_c,"
                "humidity_percent,latitude,longitude,source\n"
            )
            original_root = header + "Palakkad,2023-01-01,1,20,30,70,10.77,76.65,NASA POWER\n"
            original_processed = header + "Alappuzha,2023-01-01,2,21,31,70,9.49,76.33,NASA POWER\n"
            root_file.write_text(original_root, encoding="utf-8")
            processed_file.write_text(original_processed, encoding="utf-8")
            collector = WeatherCollector(
                base_data_dir=str(data_dir),
                client=InvalidClient(),
                registry=DatasetRegistry(metadata_dir=str(data_dir / "metadata")),
            )

            result = collector.run_ingestion(
                districts=[district],
                start_date="20240101",
                end_date="20240101",
                pause_between_calls=0,
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "no_valid_records")
            self.assertEqual(result["rainfall_anomaly_count"], 1)
            self.assertIn(
                "not a finite numeric value",
                Path(result["anomaly_file"]).read_text(encoding="utf-8"),
            )
            self.assertEqual(root_file.read_text(encoding="utf-8"), original_root)
            self.assertEqual(processed_file.read_text(encoding="utf-8"), original_processed)


if __name__ == "__main__":
    unittest.main()
