"""Unit tests for the Weather Data Module."""

import unittest
from app.backend.weather.coordinates import KERALA_DISTRICT_COORDINATES
from app.backend.weather.nasa_power import NasaPowerClient
from app.backend.dataset_manager.schemas import KERALA_DISTRICTS


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

    def test_precipitation_non_negative_clamp(self):
        """Rainfall cannot be negative."""
        client = NasaPowerClient()
        mock_raw = {
            "properties": {
                "parameter": {
                    "PRECTOTCORR": {"20230101": -0.01},  # small numerical noise
                    "T2M_MIN": {"20230101": 21.0},
                    "T2M_MAX": {"20230101": 31.0},
                    "RH2M": {"20230101": 75.0},
                }
            }
        }
        records, _ = client._parse_nasa_response(
            mock_raw,
            district="Kollam",
            latitude=8.8932,
            longitude=76.6141
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["rainfall_mm"], 0.0)


if __name__ == "__main__":
    unittest.main()
