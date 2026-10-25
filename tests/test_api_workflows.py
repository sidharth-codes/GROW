"""End-to-end service tests for ingestion and recommendation workflows."""

import tempfile
import json
import threading
import unittest
import urllib.parse
import urllib.request
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer

from app.backend.api import GrowHandler, GrowService


class TestGrowWorkflows(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = GrowService(Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dataset_upload_to_crop_recommendation(self):
        soil_csv = (
            "district,soil_type,soil_texture,drainage,soil_depth,ph_category,"
            "organic_matter_category,fertility_category\n"
            "Alappuzha,Test alluvial,Clay,Moderately drained,Deep,"
            "Slightly acidic,Moderate,Moderate\n"
        ).encode()
        soil_result = self.service.upload("soil", "soil.csv", soil_csv)
        self.assertTrue(soil_result["success"])
        self.assertEqual(soil_result["commit"]["records_committed"], 1)

        suitability_csv = (
            "district,soil_type,crop,texture_score,drainage_score,estimated_ph_score,"
            "suitability_score,ph_status,score_method\n"
            "Alappuzha,Test alluvial,Rice,90,80,70,80,Estimated,Uploaded test matrix\n"
            "Alappuzha,Test alluvial,Coconut,50,65,,57.5,Not available,Uploaded test matrix\n"
        ).encode()
        matrix_result = self.service.upload(
            "soil_crop_suitability_v2", "suitability.csv", suitability_csv
        )
        self.assertTrue(matrix_result["success"])
        recommendations = self.service.recommendations("Alappuzha", "Test alluvial")

        self.assertEqual(
            [row["crop"] for row in recommendations["recommendations"]],
            ["Rice", "Coconut"],
        )
        self.assertEqual(recommendations["recommendations"][0]["suitability_score"], 80)
        self.assertIn("heuristic", recommendations["recommendations"][0]["interpretation"].lower())
        self.assertEqual(recommendations["provenance"]["dataset"], "data/processed/soil_crop_suitability_v2.csv")

    def test_http_upload_to_crop_recommendation(self):
        soil_csv = (
            "district,soil_type,soil_texture,drainage,soil_depth,ph_category,"
            "organic_matter_category,fertility_category\n"
            "Alappuzha,Test alluvial,Clay,Moderately drained,Deep,"
            "Slightly acidic,Moderate,Moderate\n"
        )
        matrix_csv = (
            "district,soil_type,crop,texture_score,drainage_score,estimated_ph_score,"
            "suitability_score,ph_status,score_method\n"
            "Alappuzha,Test alluvial,Rice,90,80,70,80,Estimated,Uploaded test matrix\n"
        )

        with patch("app.backend.api.SERVICE", self.service):
            server = ThreadingHTTPServer(("127.0.0.1", 0), GrowHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                for dataset_id, filename, content in (
                    ("soil", "soil.csv", soil_csv),
                    ("soil_crop_suitability_v2", "suitability.csv", matrix_csv),
                ):
                    boundary = "GROW-integration-test"
                    body = (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                        "Content-Type: text/csv\r\n\r\n"
                        f"{content}\r\n--{boundary}--\r\n"
                    ).encode()
                    request = urllib.request.Request(
                        f"{base_url}/api/datasets/{dataset_id}/upload",
                        data=body,
                        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                        method="POST",
                    )
                    with urllib.request.urlopen(request) as response:
                        self.assertEqual(response.status, 201)
                        self.assertTrue(json.loads(response.read())["success"])

                query = urllib.parse.urlencode({
                    "district": "Alappuzha",
                    "soil_type": "Test alluvial",
                })
                with urllib.request.urlopen(f"{base_url}/api/recommendations?{query}") as response:
                    result = json.loads(response.read())
                self.assertEqual(result["recommendations"][0]["crop"], "Rice")
                self.assertEqual(result["recommendations"][0]["suitability_score"], 80)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_invalid_upload_is_not_promoted(self):
        bad_csv = b"district,soil_type\nAlappuzha,Incomplete\n"
        result = self.service.upload("soil", "bad.csv", bad_csv)

        self.assertFalse(result["success"])
        self.assertFalse((Path(self.temp_dir.name) / "data" / "processed" / "soil.csv").exists())

    def test_missing_prices_are_reported_as_unavailable(self):
        result = self.service.market_prices()
        self.assertFalse(result["available"])
        self.assertEqual(result["record_count"], 0)
        self.assertTrue(result["reason"])

    def test_market_prices_report_unverified_source_unit(self):
        prices_path = self.service.data_dir / "processed" / "market_prices.csv"
        prices_path.parent.mkdir(parents=True, exist_ok=True)
        prices_path.write_text(
            "date,district,market,crop,variety,min_price,max_price,modal_price,price_unit,source\n"
            "2026-10-25,Palakkad,Test Market,Rice,Common,100,120,110,"
            "UNVERIFIED_SOURCE_UNIT,DATA.GOV.IN_AGMARKNET_API\n",
            encoding="utf-8",
        )

        result = self.service.market_prices()

        self.assertTrue(result["available"])
        self.assertFalse(result["price_unit_verified"])
        self.assertIn("not labeled as INR/quintal", result["price_unit_notice"])
        self.assertEqual(
            result["records"][0]["price_unit"], "UNVERIFIED_SOURCE_UNIT"
        )

    def test_profitability_rejects_unverified_market_price_unit(self):
        price_row = {
            "date": "2026-10-25",
            "district": "Palakkad",
            "market": "Test Market",
            "crop": "Rice",
            "modal_price": "110",
            "price_unit": "UNVERIFIED_SOURCE_UNIT",
        }
        cost_row = {
            "district": "Palakkad",
            "crop": "Rice",
            "total_cost_per_hectare": "1000",
        }
        self.service.rows = lambda dataset_id: (
            {
                "market_prices": [price_row],
                "cultivation_cost": [cost_row],
                "demand": [],
                "crop_yield": [],
            }.get(dataset_id, []),
            None,
        )

        result = self.service.profitability("Palakkad", "Rice")

        self.assertFalse(result["available"])
        self.assertIn("verified market-price unit", result["missing_inputs"])

    def test_state_cost_summary_does_not_enable_profitability(self):
        summary_path = (
            Path(self.temp_dir.name)
            / "data"
            / "processed"
            / "kerala_cost_of_cultivation_summary_2022_23_2023_24.csv"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            "agriculture_year,crop,season,reported_input_cost_rs_per_ha,"
            "reported_value_of_output_rs_per_ha,currency,area_unit,"
            "source_table_label,source_url,source_status,notes\n"
            "2023-24,Paddy,Autumn,82488,117719,INR,hectare,Summary table,"
            "https://example.org/report,transcribed,State-level only\n",
            encoding="utf-8",
        )

        summary = self.service.cultivation_cost_summary()
        profitability = self.service.profitability("Alappuzha", "Paddy")

        self.assertTrue(summary["available"])
        self.assertEqual(summary["record_count"], 1)
        self.assertEqual(summary["geographic_resolution"], "State")
        self.assertFalse(profitability["available"])
        self.assertIn("matching cultivation-cost record", profitability["missing_inputs"])
        self.assertIn("matching market-price observations", profitability["missing_inputs"])

        with patch("app.backend.api.SERVICE", self.service):
            server = ThreadingHTTPServer(("127.0.0.1", 0), GrowHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{server.server_port}/api/cultivation-cost-summary"
                ) as response:
                    api_summary = json.loads(response.read())
                self.assertTrue(api_summary["available"])
                self.assertEqual(api_summary["record_count"], 1)
                self.assertEqual(api_summary["geographic_resolution"], "State")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_statewide_cost_a_is_not_used_for_profitability(self):
        cost_a_path = (
            Path(self.temp_dir.name)
            / "data"
            / "processed"
            / "kerala_statewide_cost_a_timeseries_2014_15_to_2023_24.csv"
        )
        cost_a_path.parent.mkdir(parents=True, exist_ok=True)
        cost_a_path.write_text(
            "crop,season,cost_year,cost_a_rs_per_hectare,state,source,source_page,"
            "source_url,retrieved_at,source_verification_status,notes\n"
            "Paddy,Autumn,2023-24,82488,Kerala,SYNTHETIC_TEST_FIXTURE,264,"
            "https://example.org/report,2026-10-25T00:00:00+00:00,"
            "verified_against_report_table_A5.1,Statewide only\n",
            encoding="utf-8",
        )

        api_cost_a = self.service.cultivation_cost_a()
        profitability = self.service.profitability("Alappuzha", "Paddy")

        self.assertTrue(api_cost_a["available"])
        self.assertEqual(api_cost_a["record_count"], 1)
        self.assertEqual(api_cost_a["geographic_resolution"], "State")
        self.assertFalse(profitability["available"])

        with patch("app.backend.api.SERVICE", self.service):
            server = ThreadingHTTPServer(("127.0.0.1", 0), GrowHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{server.server_port}/api/cultivation-cost-a"
                ) as response:
                    api_response = json.loads(response.read())
                self.assertTrue(api_response["available"])
                self.assertEqual(api_response["record_count"], 1)
                self.assertEqual(api_response["geographic_resolution"], "State")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_market_arrivals_upload_preserves_source_unit(self):
        fixture = (
            "observation_date,state,district,market,commodity,variety,arrival_quantity,"
            "arrival_unit,source,retrieved_at,source_record_id\n"
            "2024-06-01,Kerala,Palakkad,Test market,Rice,Test variety,1.5,tonnes,"
            "SYNTHETIC_TEST_FIXTURE,2024-06-02T00:00:00Z,test-record-1\n"
        ).encode()

        result = self.service.upload("market_arrivals", "arrivals.csv", fixture)
        arrivals = self.service.market_arrivals("Palakkad", "Rice")
        profitability = self.service.profitability("Palakkad", "Rice")

        self.assertTrue(result["success"], result.get("validation"))
        self.assertTrue(arrivals["available"])
        self.assertEqual(arrivals["records"][0]["arrival_unit"], "tonnes")
        self.assertEqual(arrivals["records"][0]["arrival_quantity"], "1.5")
        self.assertFalse(profitability["available"])

        with patch("app.backend.api.SERVICE", self.service):
            server = ThreadingHTTPServer(("127.0.0.1", 0), GrowHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                query = urllib.parse.urlencode({"district": "Palakkad", "commodity": "Rice"})
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{server.server_port}/api/market-arrivals?{query}"
                ) as response:
                    api_arrivals = json.loads(response.read())
                self.assertTrue(api_arrivals["available"])
                self.assertEqual(api_arrivals["records"][0]["arrival_unit"], "tonnes")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_market_arrivals_without_source_unit_are_rejected(self):
        fixture = (
            "observation_date,state,district,market,commodity,variety,arrival_quantity,"
            "arrival_unit,source,retrieved_at,source_record_id\n"
            "2024-06-01,Kerala,Palakkad,Test market,Rice,Test variety,1.5,,"
            "SYNTHETIC_TEST_FIXTURE,2024-06-02T00:00:00Z,test-record-1\n"
        ).encode()

        result = self.service.upload("market_arrivals", "arrivals.csv", fixture)

        self.assertFalse(result["success"])
        self.assertFalse(
            (Path(self.temp_dir.name) / "data" / "processed" / "market_arrivals.csv").exists()
        )

    def test_yield_baseline_comes_from_saved_model_artifact(self):
        result = GrowService().yield_history("Alappuzha", "Banana")

        self.assertIsNotNone(result["estimate"])
        self.assertGreater(result["estimate"]["value_kg_per_hectare"], 0)
        self.assertEqual(result["estimate"]["model"], "baseline_district_crop_mean")
        self.assertIn("not a weather-aware", result["estimate"]["interpretation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
