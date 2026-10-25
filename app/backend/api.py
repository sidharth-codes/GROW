"""Small standard-library HTTP API and static frontend server for GROW."""

import json
import mimetypes
import sys
import tempfile
from collections import defaultdict
from datetime import date
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.dataset_manager.ingestion import DatasetIngestionService
from app.backend.dataset_manager.registry import DatasetRegistry
from app.backend.dataset_manager.schemas import DATASET_SCHEMAS, KERALA_DISTRICTS
from app.backend.ml.utils import read_csv_as_dicts
from app.backend.price_ingestion.normalizer import UNVERIFIED_SOURCE_UNIT


class GrowService:
    """Reads project datasets and model artifacts for the web application."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.data_dir = self.root / "data"
        self.models_dir = self.root / "models"
        self.registry = DatasetRegistry(
            metadata_dir=str(self.data_dir / "metadata")
        )
        self.ingestion = DatasetIngestionService(
            base_data_dir=str(self.data_dir),
            registry=self.registry,
        )

    def data_path(self, dataset_id):
        schema = DATASET_SCHEMAS.get(dataset_id)
        if not schema:
            raise KeyError(dataset_id)
        filename = schema["source_info"].expected_filename
        for path in (self.data_dir / "processed" / filename, self.data_dir / filename):
            if path.is_file() and path.stat().st_size > 0:
                return path
        return None

    def rows(self, dataset_id):
        path = self.data_path(dataset_id)
        if path is None:
            return [], None
        return read_csv_as_dicts(str(path)), path

    def model_meta(self, name):
        path = self.models_dir / name
        if not path.is_file():
            return None
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    def datasets(self):
        result = []
        for dataset_id, registered in self.registry.datasets.items():
            path = self.data_path(dataset_id)
            meta = dict(registered)
            meta["file_available"] = path is not None
            meta["active_path"] = str(path.relative_to(self.root)).replace("\\", "/") if path else None
            if path:
                meta["record_count"] = sum(1 for _ in path.open(encoding="utf-8", errors="replace")) - 1
                if meta["validation_status"] == "passed" and meta["status"] != "partially_available":
                    meta["status"] = "available"
            elif meta.get("status") not in ("awaiting_upload", "validation_failed"):
                meta["status"] = "not_collected"
            result.append(meta)
        return result

    def dashboard(self):
        datasets = self.datasets()
        crops, _ = self.rows("crops")
        soils, _ = self.rows("soil")
        suitability, _ = self.rows("soil_crop_suitability_v2")
        weather, weather_path = self.rows("weather")
        yields, _ = self.rows("crop_yield")
        prices, _ = self.rows("market_prices")
        arrivals, _ = self.rows("market_arrivals")
        models = {
            "soil": self.model_meta("soil_clustering_meta.json"),
            "yield": self.model_meta("crop_yield_model_meta.json"),
            "price": self.model_meta("market_price_model_meta.json"),
        }
        return {
            "as_of": date.today().isoformat(),
            "metrics": {
                "districts_covered": len({r.get("district") for r in soils}),
                "crops_catalogued": len(crops),
                "suitability_records": len(suitability),
                "weather_records": len(weather),
                "yield_records": len(yields),
                "price_records": len(prices),
                "market_arrival_records": len(arrivals),
                "state_cost_summary_records": len(self.rows("cultivation_cost_summary")[0]),
                "state_cost_a_records": len(self.rows("cultivation_cost_a")[0]),
                "datasets_available": sum(item["file_available"] for item in datasets),
                "datasets_total": len(datasets),
            },
            "weather_latest_date": max((r.get("date", "") for r in weather), default=None),
            "weather_source": "NASA POWER" if weather_path else None,
            "models": models,
            "data_gaps": [
                item["name"] for item in datasets if not item["file_available"]
            ],
            "limitations": [
                "Crop suitability is a rule-based heuristic, not a field-calibrated ML prediction.",
                "Soil profiles are district-level qualitative references, not farm-specific laboratory tests.",
                "AGMARKNET market prices are available for one date only, and itemized district-level cultivation costs are unavailable; profitability is not calculated.",
                "Market arrivals are physical reported quantities, not a direct measure of demand.",
                "Weather observations are historical NASA POWER gridded estimates, not live forecasts.",
            ],
        }

    def crops(self):
        records, _ = self.rows("crops")
        if not records:
            raise RuntimeError("Crop catalog is unavailable. Upload a valid crops.csv dataset.")
        return records

    def recommendations(self, district, soil_type=None):
        if not district:
            raise ValueError("Select a district to request crop recommendations.")
        soils, _ = self.rows("soil")
        matrix, path = self.rows("soil_crop_suitability_v2")
        if not soils or not matrix:
            raise RuntimeError("Soil profiles or the suitability matrix are unavailable; no recommendation can be calculated.")
        matching_soils = [
            soil for soil in soils
            if soil["district"] == district and (not soil_type or soil["soil_type"] == soil_type)
        ]
        if not matching_soils:
            raise LookupError(f"No soil profile is recorded for {district}" + (f" / {soil_type}." if soil_type else "."))
        by_crop = defaultdict(list)
        soil_names = {soil["soil_type"] for soil in matching_soils}
        for row in matrix:
            if row["district"] == district and row["soil_type"] in soil_names:
                by_crop[row["crop"]].append(row)
        if not by_crop:
            raise RuntimeError(f"No suitability scores are recorded for {district} and the selected soil.")
        ranked = []
        for crop, entries in by_crop.items():
            # If multiple soil profiles are selected, report the strongest profile
            # and keep its source profile visible rather than averaging unlike soils.
            best = max(entries, key=lambda item: float(item["suitability_score"]))
            ranked.append({
                **best,
                "suitability_score": float(best["suitability_score"]),
                "texture_score": float(best["texture_score"]),
                "drainage_score": float(best["drainage_score"]),
                "estimated_ph_score": float(best["estimated_ph_score"]) if best.get("estimated_ph_score") else None,
                "interpretation": "Heuristic compatibility score; not a probability or guaranteed outcome.",
            })
        ranked.sort(key=lambda item: item["suitability_score"], reverse=True)
        return {
            "district": district,
            "soil_type": soil_type,
            "recommendations": ranked,
            "provenance": {
                "dataset": str(path.relative_to(self.root)).replace("\\", "/"),
                "method": "Equal-weight soil texture, drainage, and estimated pH heuristic",
                "profile_source": "District-level qualitative soil profile",
            },
            "limitations": [
                "pH compatibility is estimated from qualitative soil categories.",
                "Scores do not include farm-specific soil tests, water access, pest pressure, or crop-calendar constraints.",
                "The score ranks compatibility in the available matrix only; it is not a yield or profit forecast.",
            ],
        }

    def soil_analysis(self, district):
        soils, _ = self.rows("soil")
        if not soils:
            raise RuntimeError("Soil profile dataset is unavailable.")
        records = [row for row in soils if not district or row["district"] == district]
        if not records:
            raise LookupError(f"No soil profile is recorded for {district}.")
        result = {"district": district, "profiles": records, "cluster": None}
        artifact = self.models_dir / "soil_clustering.joblib"
        if artifact.is_file():
            try:
                import joblib
                bundle = joblib.load(artifact)
                labels = bundle["kmeans"].predict(
                    bundle["encoder"].transform([[
                        records[0][column] for column in bundle["feature_columns"]
                    ]])
                )
                result["cluster"] = {
                    "id": int(labels[0]),
                    "label": f"Indicative soil group {int(labels[0]) + 1}",
                    "silhouette": (self.model_meta("soil_clustering_meta.json") or {}).get("silhouette"),
                    "warning": "Cluster IDs are interpretive and are not quality rankings.",
                }
            except (KeyError, ValueError, OSError, ImportError) as exc:
                result["cluster_error"] = f"Saved soil model could not be applied: {exc}"
        result["limitations"] = [
            "Profile values are regional qualitative benchmarks, not farm-level tests.",
            "The clustering model uses only 23 soil records and five categorical features.",
        ]
        result["provenance"] = "data/processed/soil.csv and models/soil_clustering.joblib"
        return result

    def weather(self, district):
        if not district:
            raise ValueError("Select a district to view weather history.")
        records, _ = self.rows("weather")
        if not records:
            raise RuntimeError("Weather history is unavailable.")
        filtered = [r for r in records if r["district"] == district]
        if not filtered:
            raise LookupError(f"No weather observations are available for {district}.")
        filtered.sort(key=lambda row: row["date"])
        latest = filtered[-30:]
        numeric = ("rainfall_mm", "temperature_min_c", "temperature_max_c", "humidity_percent")
        summary = {}
        for key in numeric:
            vals = [float(r[key]) for r in latest]
            summary[key] = round(sum(vals) / len(vals), 2)
        return {
            "district": district,
            "record_count": len(filtered),
            "date_range": [filtered[0]["date"], filtered[-1]["date"]],
            "latest_30_day_average": summary,
            "observations": latest,
            "provenance": "NASA POWER daily gridded estimates",
            "limitations": ["Historical observations only; this is not a current condition or forecast."],
        }

    def yield_history(self, district=None, crop=None):
        records, _ = self.rows("crop_yield")
        if not records:
            raise RuntimeError("Historical yield dataset is unavailable.")
        filtered = [
            row for row in records
            if (not district or row["district"] == district)
            and (not crop or row["crop"] == crop)
        ]
        filtered.sort(key=lambda row: (row["year"], row["district"], row["crop"]))
        for row in filtered:
            for key in ("area_hectares", "production_tonnes", "yield_kg_per_hectare"):
                row[key] = float(row[key]) if row.get(key) else None
        model = self.model_meta("crop_yield_model_meta.json")
        estimate = None
        estimate_error = None
        if district and crop:
            if model and model.get("best_model") == "baseline_district_crop_mean":
                artifact = self.models_dir / "crop_yield_model.joblib"
                if artifact.is_file():
                    try:
                        import joblib
                        bundle = joblib.load(artifact)
                        value = bundle["baseline_means"].get((crop, district))
                        if value is not None:
                            estimate = {
                                "value_kg_per_hectare": float(value),
                                "model": "baseline_district_crop_mean",
                                "training_period": model.get("train_years"),
                                "held_out_metrics": model.get("metrics", {}).get("baseline_district_crop_mean"),
                                "interpretation": (
                                    "Training-period district/crop mean from the saved model artifact; "
                                    "not a weather-aware or season-specific forecast."
                                ),
                            }
                        else:
                            estimate_error = "The saved model has no training baseline for this crop and district."
                    except (FileNotFoundError, ImportError, KeyError, OSError, ValueError) as exc:
                        estimate_error = f"Saved yield model could not be applied: {exc}"
                else:
                    estimate_error = "The saved yield model artifact is unavailable."
            else:
                estimate_error = "No supported saved best-model configuration is available for this estimate."
        return {
            "records": filtered[-300:],
            "total_matching_records": len(filtered),
            "filters": {"district": district, "crop": crop},
            "estimate": estimate,
            "estimate_error": estimate_error,
            "provenance": "DES Kerala agricultural statistics; district-level observed records.",
            "limitations": [
                "District averages do not represent a specific farm.",
                "The optional estimate is a training-period district/crop average, not a weather-aware seasonal forecast.",
                "The model has moderate data adequacy and a limited weather-joined time period.",
            ],
            "model": model,
        }

    def market_prices(self, district=None, crop=None):
        records, _ = self.rows("market_prices")
        if not records:
            meta = self.model_meta("market_price_model_meta.json") or {}
            return {
                "available": False,
                "records": [],
                "record_count": 0,
                "reason": meta.get("reason", "No market price records have been ingested."),
                "requirements": {
                    "minimum_records": meta.get("threshold_records", 500),
                    "minimum_months": meta.get("threshold_months", 24),
                },
                "provenance": "Agmarknet / DMI data required",
            }
        filtered = [
            row for row in records
            if (not district or row["district"] == district)
            and (not crop or row["crop"] == crop)
        ]
        filtered.sort(key=lambda row: row["date"])
        api_sourced = any(
            str(row.get("source", "")).startswith("DATA.GOV.IN")
            for row in filtered
        )
        price_unit_verified = all(
            str(row.get("price_unit", "")).casefold()
            != UNVERIFIED_SOURCE_UNIT.casefold()
            for row in filtered
        )
        return {
            "available": bool(filtered),
            "records": filtered[-300:],
            "record_count": len(filtered),
            "reason": None if filtered else "No records match the selected filters.",
            "price_unit_verified": price_unit_verified,
            "price_unit_notice": (
                None
                if price_unit_verified
                else "The source does not report a price unit; values are shown unchanged and are not labeled as INR/quintal."
            ),
            "provenance": (
                "Data.gov.in AGMARKNET API records"
                if api_sourced
                else "Uploaded market-price source records"
            ),
            "model": self.model_meta("market_price_model_meta.json"),
        }

    def cultivation_cost_summary(self):
        records, path = self.rows("cultivation_cost_summary")
        return {
            "available": bool(records),
            "records": records,
            "record_count": len(records),
            "geographic_resolution": "State",
            "source": "Department of Economics & Statistics, Government of Kerala",
            "source_file": str(path.relative_to(self.root)).replace("\\", "/") if path else None,
            "limitations": [
                "This is a statewide report summary, not district- or farm-specific cost data.",
                "Reported input cost and value of output are report-defined metrics, not full cost, profit, or ROI.",
                "Values were transcribed from report transcripts and require verification against the original reports.",
                "Blank source values remain missing and are not treated as zero.",
            ],
        }

    def cultivation_cost_a(self):
        records, path = self.rows("cultivation_cost_a")
        return {
            "available": bool(records),
            "records": records,
            "record_count": len(records),
            "geographic_resolution": "State",
            "unit": "INR/hectare",
            "source": "Kerala Department of Economics & Statistics",
            "source_table": "A5.1 Cropwise timeseries data, printed page 264",
            "source_file": str(path.relative_to(self.root)).replace("\\", "/") if path else None,
            "verification_status": "All source values cross-checked against the official 2023-24 report.",
            "limitations": [
                "Cost A is not full Cost C, district-specific cost, profit, or ROI.",
                "Zero values are preserved as printed and may mean not reported/not covered.",
                "This dataset is not used for profitability calculations.",
            ],
        }

    def market_arrivals(self, district=None, commodity=None):
        records, _ = self.rows("market_arrivals")
        filtered = [
            row for row in records
            if (not district or row["district"] == district)
            and (not commodity or row["commodity"] == commodity)
        ]
        filtered.sort(key=lambda row: row["observation_date"])
        return {
            "available": bool(filtered),
            "records": filtered[-300:],
            "record_count": len(filtered),
            "reason": None if filtered else "No authentic market-arrival records match the selected filters.",
            "provenance": "AGMARKNET records; source units are retained without conversion.",
            "limitations": [
                "Arrival quantity is not converted or interpreted as demand.",
                "Only records with an explicit source unit should be ingested.",
            ],
        }

    def profitability(self, district, crop):
        cost_rows, _ = self.rows("cultivation_cost")
        price_rows, _ = self.rows("market_prices")
        demand_rows, _ = self.rows("demand")
        if not district or not crop:
            return {
                "available": False,
                "reason": "Select both district and crop to check whether matching source records exist.",
                "missing_inputs": ["district and crop selection"],
                "cost_data_records": len(cost_rows),
                "price_data_records": len(price_rows),
                "demand_data_records": len(demand_rows),
            }
        cost = next((r for r in reversed(cost_rows) if r.get("district") == district and r.get("crop") == crop), None)
        prices = [r for r in price_rows if r.get("district") == district and r.get("crop") == crop]
        demand = [r for r in demand_rows if r.get("district") == district and r.get("crop") == crop]
        if not cost or not prices:
            missing = []
            if not cost:
                missing.append("matching cultivation-cost record")
            if not prices:
                missing.append("matching market-price observations")
            return {
                "available": False,
                "reason": "Cannot calculate profitability without " + " and ".join(missing) + ".",
                "missing_inputs": missing,
                "cost_data_records": len(cost_rows),
                "price_data_records": len(price_rows),
                "demand_data_records": len(demand_rows),
            }
        if any(
            str(row.get("price_unit", "")).casefold()
            == UNVERIFIED_SOURCE_UNIT.casefold()
            for row in prices
        ):
            return {
                "available": False,
                "reason": (
                    "Cannot calculate profitability because the source price unit "
                    "is unverified."
                ),
                "missing_inputs": ["verified market-price unit"],
                "cost_data_records": len(cost_rows),
                "price_data_records": len(price_rows),
                "demand_data_records": len(demand_rows),
            }
        latest_price = max(prices, key=lambda row: row["date"])
        latest_price_value = float(latest_price["modal_price"])
        output = None
        yield_rows, _ = self.rows("crop_yield")
        historical = [r for r in yield_rows if r["district"] == district and r["crop"] == crop]
        if historical:
            output = float(max(historical, key=lambda row: row["year"])["yield_kg_per_hectare"])
        if output is None:
            return {"available": False, "reason": "Historical yield is unavailable for this district and crop.", "missing_inputs": ["historical yield"]}
        cost_value = float(cost["total_cost_per_hectare"])
        # Yield is kg/ha and market quotes are INR/quintal (100 kg).
        gross_revenue = (output / 100.0) * latest_price_value
        return {
            "available": True,
            "district": district,
            "crop": crop,
            "yield_kg_per_hectare": output,
            "price_inr_per_quintal": latest_price_value,
            "price_date": latest_price["date"],
            "cost_inr_per_hectare": cost_value,
            "gross_revenue_inr_per_hectare": round(gross_revenue, 2),
            "indicative_margin_inr_per_hectare": round(gross_revenue - cost_value, 2),
            "demand_records": len(demand),
            "provenance": ["Historical yield", "Uploaded cultivation costs", "Uploaded market prices"],
            "limitations": ["Gross margin excludes unrecorded costs and is not a guaranteed farm profit."],
        }

    def model_performance(self):
        return {
            "soil": self.model_meta("soil_clustering_meta.json"),
            "yield": self.model_meta("crop_yield_model_meta.json"),
            "price": self.model_meta("market_price_model_meta.json"),
        }

    def upload(self, dataset_id, filename, content):
        if dataset_id not in DATASET_SCHEMAS:
            raise KeyError(f"Unknown dataset: {dataset_id}")
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as stream:
            stream.write(content)
            staged_path = Path(stream.name)
        try:
            inspection = self.ingestion.inspect_and_stage_upload(str(staged_path), dataset_id, filename)
            if not inspection.get("accepted"):
                return {"success": False, "validation": inspection}
            committed = self.ingestion.commit_upload(str(staged_path), dataset_id, filename)
            return {"success": committed["success"], "validation": inspection, "commit": committed}
        finally:
            staged_path.unlink(missing_ok=True)


SERVICE = GrowService()


class GrowHandler(BaseHTTPRequestHandler):
    server_version = "GROW/1.0"

    def _json(self, value, status=200):
        payload = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, message, status):
        self._json({"error": message}, status)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        district = query.get("district", [None])[0]
        crop = query.get("crop", [None])[0]
        try:
            routes = {
                "/api/health": lambda: {"status": "ok"},
                "/api/dashboard": SERVICE.dashboard,
                "/api/datasets": SERVICE.datasets,
                "/api/crops": SERVICE.crops,
                "/api/districts": lambda: KERALA_DISTRICTS,
                "/api/soil": lambda: SERVICE.soil_analysis(district),
                "/api/weather": lambda: SERVICE.weather(district),
                "/api/yield": lambda: SERVICE.yield_history(district, crop),
                "/api/market-prices": lambda: SERVICE.market_prices(district, crop),
                "/api/market-arrivals": lambda: SERVICE.market_arrivals(
                    district,
                    query.get("commodity", [None])[0],
                ),
                "/api/cultivation-cost-summary": SERVICE.cultivation_cost_summary,
                "/api/cultivation-cost-a": SERVICE.cultivation_cost_a,
                "/api/profitability": lambda: SERVICE.profitability(district, crop),
                "/api/models": SERVICE.model_performance,
            }
            if parsed.path == "/api/recommendations":
                result = SERVICE.recommendations(district, query.get("soil_type", [None])[0])
            elif parsed.path in routes:
                result = routes[parsed.path]()
            elif parsed.path.startswith("/api/datasets/") and parsed.path.endswith("/guidance"):
                dataset_id = parsed.path.split("/")[3]
                result = SERVICE.ingestion.get_manual_download_guidance(dataset_id)
                if "error" in result:
                    return self._error(result["error"], 404)
            elif parsed.path == "/" or not parsed.path.startswith("/api/"):
                return self._static(parsed.path)
            else:
                return self._error("API route not found.", 404)
            self._json(result)
        except ValueError as exc:
            self._error(str(exc), 400)
        except LookupError as exc:
            self._error(str(exc), 404)
        except RuntimeError as exc:
            self._error(str(exc), 503)
        except (OSError, json.JSONDecodeError) as exc:
            self._error(f"Unable to read GROW data: {exc}", 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/datasets/") and parsed.path.endswith("/upload"):
            dataset_id = parsed.path.split("/")[3]
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > DatasetIngestionService.MAX_FILE_SIZE_BYTES + 1024 * 1024:
                return self._error("Upload is empty or exceeds the 50 MB limit.", 413)
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                return self._error("Upload must use multipart/form-data.", 415)
            message = BytesParser(policy=policy.default).parsebytes(
                f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode()
                + self.rfile.read(length)
            )
            part = next((item for item in message.iter_parts() if item.get_filename()), None)
            if part is None:
                return self._error("Choose a CSV file to upload.", 400)
            try:
                result = SERVICE.upload(dataset_id, Path(part.get_filename()).name, part.get_payload(decode=True))
            except KeyError as exc:
                return self._error(str(exc), 404)
            except (OSError, ValueError) as exc:
                return self._error(f"Upload failed: {exc}", 400)
            return self._json(result, 201 if result["success"] else 422)
        if parsed.path == "/api/recommendations":
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                result = SERVICE.recommendations(payload.get("district"), payload.get("soil_type"))
                return self._json(result)
            except ValueError as exc:
                return self._error(str(exc), 400)
            except LookupError as exc:
                return self._error(str(exc), 404)
            except RuntimeError as exc:
                return self._error(str(exc), 503)
        self._error("API route not found.", 404)

    def _static(self, requested_path):
        relative = "index.html" if requested_path in ("", "/") else requested_path.lstrip("/")
        target = (ROOT / "app" / "frontend" / relative).resolve()
        frontend_root = (ROOT / "app" / "frontend").resolve()
        if frontend_root not in target.parents or not target.is_file():
            target = frontend_root / "index.html"
        data = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format_string, *args):
        print(f"[GROW] {self.address_string()} - {format_string % args}")


def main():
    host = "127.0.0.1"
    port = 8000
    print(f"GROW running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), GrowHandler).serve_forever()


if __name__ == "__main__":
    main()
