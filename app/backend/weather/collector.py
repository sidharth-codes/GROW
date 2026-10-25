"""Weather data collection pipeline for GROW.

Ingests daily NASA POWER agro-meteorological data for all 14 Kerala districts
across the 2015-2025 observation window.
"""

import argparse
import csv
import json
import logging
import math
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.weather.coordinates import KERALA_DISTRICT_COORDINATES
from app.backend.weather.nasa_power import NasaPowerClient
from app.backend.dataset_manager.validator import DatasetValidator
from app.backend.dataset_manager.registry import DatasetRegistry

logger = logging.getLogger("grow.weather")


class WeatherCollector:
    """Orchestrates multi-district weather ingestion and validation."""

    def __init__(
        self,
        base_data_dir: str = "data",
        client: Optional[NasaPowerClient] = None,
        validator: Optional[DatasetValidator] = None,
        registry: Optional[DatasetRegistry] = None,
    ):
        self.data_dir = Path(base_data_dir)
        self.raw_dir = self.data_dir / "raw" / "weather"
        self.processed_dir = self.data_dir / "processed"
        self.metadata_dir = self.data_dir / "metadata"

        self.client = client or NasaPowerClient(raw_storage_dir=str(self.raw_dir))
        self.validator = validator or DatasetValidator()
        self.registry = registry or DatasetRegistry(metadata_dir=str(self.metadata_dir))

    def run_ingestion(
        self,
        districts: Optional[List[str]] = None,
        start_date: str = "20150101",
        end_date: str = "20251231",
        force_refresh: bool = False,
        pause_between_calls: float = 1.0,
    ) -> Dict[str, Any]:
        """Ingest historical daily weather for specified or all Kerala districts."""
        target_districts = districts or list(KERALA_DISTRICT_COORDINATES.keys())
        weather_schema = self.validator.schemas.get("weather")
        rainfall_column = next(
            (
                column for column in weather_schema["columns"]
                if column.name == "rainfall_mm"
            ),
            None,
        ) if weather_schema else None
        if rainfall_column is None:
            return {
                "success": False,
                "status": "schema_configuration_error",
                "error": "Weather schema does not define a rainfall_mm column.",
            }

        print(f"\n{'='*80}")
        print(
            "GROW WEATHER INGESTION: NASA POWER "
            f"({start_date[:4]}-{start_date[4:6]}-{start_date[6:]} to "
            f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]})"
        )
        print(f"Target Locations: {len(target_districts)} Kerala districts")
        print(f"{'='*80}\n")

        all_records: List[Dict[str, Any]] = []
        successful_locations: List[str] = []
        failed_locations: List[Dict[str, Any]] = []
        rainfall_anomalies: List[Dict[str, Any]] = []
        stats_by_district: Dict[str, Any] = {}

        seen_keys = set()
        duplicates_skipped = 0

        total_districts = len(target_districts)
        for idx, district in enumerate(target_districts, 1):
            if district not in KERALA_DISTRICT_COORDINATES:
                print(f"[{idx}/{total_districts}] SKIP: Unknown district '{district}'")
                continue

            geo = KERALA_DISTRICT_COORDINATES[district]
            lat = geo["latitude"]
            lon = geo["longitude"]

            print(f"[{idx}/{total_districts}] Fetching {district} (lat={lat:.4f}, lon={lon:.4f})...", end="", flush=True)

            success, records, meta = self.client.fetch_district_daily(
                district=district,
                latitude=lat,
                longitude=lon,
                start_date=start_date,
                end_date=end_date,
                force_refresh=force_refresh,
            )

            if success:
                successful_locations.append(district)
                source_type = meta.get("source_type", "api")
                accepted_records = []
                parameter_metadata = meta.get("parameter_metadata", {})
                precipitation_unit = (
                    parameter_metadata.get("PRECTOTCORR", {}).get("units")
                    if isinstance(parameter_metadata, dict)
                    else None
                )

                for record in records:
                    raw_rainfall = record.get("rainfall_mm")
                    try:
                        rainfall_value = float(raw_rainfall)
                    except (TypeError, ValueError):
                        rainfall_value = math.nan

                    reason = None
                    bound_unit = (
                        precipitation_unit
                        or rainfall_column.unit
                        or ""
                    )
                    if not math.isfinite(rainfall_value):
                        reason = "Rainfall is not a finite numeric value."
                    elif rainfall_column.min_value is not None and rainfall_value < rainfall_column.min_value:
                        reason = (
                            f"Rainfall is below schema minimum "
                            f"{rainfall_column.min_value} {bound_unit}."
                        ).strip()
                    elif rainfall_column.max_value is not None and rainfall_value > rainfall_column.max_value:
                        reason = (
                            f"Rainfall exceeds schema maximum "
                            f"{rainfall_column.max_value} {bound_unit}."
                        ).strip()

                    if reason:
                        rainfall_anomalies.append({
                            "district": record.get("district", district),
                            "date": record.get("date", ""),
                            "rainfall_mm": raw_rainfall,
                            "unit": precipitation_unit or rainfall_column.unit or "",
                            "source": record.get("source", ""),
                            "reason": reason,
                            "raw_response_path": meta.get("cache_path", ""),
                        })
                    else:
                        accepted_records.append(record)

                print(
                    f" OK: {len(records)} days extracted, "
                    f"{len(accepted_records)} passed rainfall bounds "
                    f"({source_type})."
                )

                # Deduplicate and append
                for r in accepted_records:
                    key = (r["district"], r["date"])
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_records.append(r)
                    else:
                        duplicates_skipped += 1

                stats_by_district[district] = {
                    "records": len(records),
                    "accepted_records": len(accepted_records),
                    "source": source_type,
                    "missing_days": meta.get("missing_precipitation_days", 0),
                    "missing_tmin_days": meta.get("missing_tmin_days", 0),
                    "missing_tmax_days": meta.get("missing_tmax_days", 0),
                    "missing_rh_days": meta.get("missing_rh_days", 0),
                    "time_standard": meta.get("time_standard"),
                    "provider_api_version": meta.get("provider_api_version"),
                    "parameter_metadata": parameter_metadata,
                }

                # Polite pause to avoid rate limit
                if source_type == "nasa_power_api" and idx < total_districts:
                    time.sleep(pause_between_calls)

            else:
                err_msg = meta.get("error", "Unknown error")
                print(f" FAILED -> {err_msg}")
                failed_locations.append({
                    "district": district,
                    "error": err_msg,
                    "fallback": meta.get("manual_fallback_url"),
                })

        anomaly_path = None
        if rainfall_anomalies:
            anomaly_path = self.metadata_dir / (
                f"weather_validation_anomalies_{start_date}_{end_date}_"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            )
            anomaly_path.parent.mkdir(parents=True, exist_ok=True)
            anomaly_temp = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    newline="",
                    encoding="utf-8",
                    dir=anomaly_path.parent,
                    prefix=f".{anomaly_path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    anomaly_temp = Path(stream.name)
                    writer = csv.DictWriter(
                        stream,
                        fieldnames=[
                            "district", "date", "rainfall_mm", "unit",
                            "source", "reason", "raw_response_path",
                        ],
                    )
                    writer.writeheader()
                    writer.writerows(rainfall_anomalies)
                os.replace(anomaly_temp, anomaly_path)
            finally:
                if anomaly_temp:
                    anomaly_temp.unlink(missing_ok=True)

        print(f"\nIngestion summary:")
        print(f"  - Successful districts: {len(successful_locations)} / {total_districts}")
        print(f"  - Failed districts:     {len(failed_locations)} / {total_districts}")
        print(f"  - Total daily records:  {len(all_records):,}")
        print(f"  - Duplicate entries:    {duplicates_skipped}")

        if failed_locations:
            return {
                "success": False,
                "status": "download_failed",
                "error": "Weather download failed for one or more requested districts; existing datasets were preserved.",
                "successful_locations": successful_locations,
                "failed_locations": failed_locations,
            }

        if not all_records:
            return {
                "success": False,
                "status": "no_valid_records",
                "error": "No weather records could be retrieved.",
                "failed_locations": failed_locations,
                "rainfall_anomaly_count": len(rainfall_anomalies),
                "anomaly_file": str(anomaly_path) if anomaly_path else None,
            }

        # Sort records by district and date
        all_records.sort(key=lambda x: (x["district"], x["date"]))

        # Write to processed and root CSV
        fieldnames = [
            "district",
            "date",
            "rainfall_mm",
            "temperature_min_c",
            "temperature_max_c",
            "humidity_percent",
            "latitude",
            "longitude",
            "source",
        ]

        processed_csv = self.processed_dir / "weather.csv"
        root_csv = self.data_dir / "weather.csv"
        existing_csv = next(
            (
                path for path in (processed_csv, root_csv)
                if path.is_file() and path.stat().st_size > 0
            ),
            None,
        )
        if existing_csv:
            existing_validation = self.validator.validate_file(str(existing_csv), "weather")
            if not existing_validation.is_valid:
                return {
                    "success": False,
                    "status": "existing_dataset_invalid",
                    "error": (
                        f"Existing weather dataset failed validation and was preserved: "
                        f"{existing_csv}"
                    ),
                    "validation": existing_validation.to_dict(),
                    "failed_locations": failed_locations,
                }
            with existing_csv.open("r", encoding="utf-8", newline="") as stream:
                existing_records = list(csv.DictReader(stream))
            merged_records = {
                (row["district"], row["date"]): {
                    name: row.get(name, "") for name in fieldnames
                }
                for row in existing_records
            }
            merged_records.update({
                (record["district"], record["date"]): record
                for record in all_records
            })
            all_records = list(merged_records.values())
            all_records.sort(key=lambda record: (record["district"], record["date"]))

        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        staged_paths: Dict[Path, Path] = {}
        backup_paths: Dict[Path, Path] = {}
        promoted_paths: List[Path] = []
        preserved_backups = set()
        try:
            for target in (processed_csv, root_csv):
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    newline="",
                    encoding="utf-8",
                    dir=target.parent,
                    prefix=f".{target.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    staged_paths[target] = Path(stream.name)
                    writer = csv.DictWriter(stream, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_records)

            print("\nValidating generated weather dataset...")
            val_result = self.validator.validate_file(str(staged_paths[processed_csv]), "weather")
            if not val_result.is_valid:
                return {
                    "success": False,
                    "status": "validation_failed",
                    "error": "Generated weather dataset failed validation; existing datasets were preserved.",
                    "validation": val_result.to_dict(),
                    "failed_locations": failed_locations,
                }

            for target in (processed_csv, root_csv):
                if target.exists():
                    descriptor, backup_name = tempfile.mkstemp(
                        dir=target.parent,
                        prefix=f".{target.name}.",
                        suffix=".bak",
                    )
                    os.close(descriptor)
                    backup_path = Path(backup_name)
                    backup_paths[target] = backup_path
                    shutil.copy2(target, backup_path)

            try:
                for target in (processed_csv, root_csv):
                    os.replace(staged_paths[target], target)
                    promoted_paths.append(target)
            except OSError as exc:
                rollback_errors = []
                for target in reversed(promoted_paths):
                    try:
                        if target in backup_paths:
                            os.replace(backup_paths[target], target)
                        else:
                            target.unlink(missing_ok=True)
                    except OSError as rollback_error:
                        rollback_errors.append(f"{target}: {rollback_error}")
                        if target in backup_paths:
                            preserved_backups.add(backup_paths[target])
                if rollback_errors:
                    raise OSError(
                        f"Dataset promotion failed ({exc}); rollback also failed: "
                        + "; ".join(rollback_errors)
                    ) from exc
                return {
                    "success": False,
                    "status": "promotion_failed",
                    "error": f"Could not promote validated weather dataset: {exc}",
                    "failed_locations": failed_locations,
                }
        finally:
            for temporary_path in staged_paths.values():
                temporary_path.unlink(missing_ok=True)
            for backup_path in backup_paths.values():
                if backup_path not in preserved_backups:
                    backup_path.unlink(missing_ok=True)

        print(f"\nSaved {len(all_records):,} records to:")
        print(f"  1. {processed_csv}")
        print(f"  2. {root_csv}")

        print(f"Validation status: {'PASS (Valid)' if val_result.is_valid else 'FAIL (Errors)'}")
        if val_result.errors:
            for e in val_result.errors[:5]:
                print(f"  [X] {e}")

        # Generate Data Quality Report
        report_md = self.validator.generate_quality_report_markdown(
            "weather", str(processed_csv), val_result
        )
        # Add geographic and observational details to report
        report_md += "\n\n## Geographical Coverage and Methodology\n\n"
        report_md += (
            "Observations are derived from NASA POWER's Agroclimatology (AG) daily archive, "
            "based on Modern-Era Retrospective Analysis for Research and Applications (MERRA-2) "
            "and Goddard Earth Observing System (GEOS) satellite-reanalysis models (~0.5° resolution).\n\n"
            "**Representative Coordinates:**\n\n"
            "| District | Latitude | Longitude | Elevation | Region |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
        )
        for d in successful_locations:
            g = KERALA_DISTRICT_COORDINATES[d]
            report_md += f"| {d} | {g['latitude']:.4f}°N | {g['longitude']:.4f}°E | {g['elevation_m']} m | {g['region']} |\n"

        report_md += (
            "\n> [!NOTE]\n"
            "> Gridded satellite-reanalysis estimates represent spatial cell averages (~50 km grid box) "
            "and may not match point observations from IMD surface weather stations or extreme micro-climatic rain shadows.\n"
        )
        observation_start = min(record["date"] for record in all_records)
        observation_end = max(record["date"] for record in all_records)
        fetched_record_count = sum(item["records"] for item in stats_by_district.values())
        accepted_record_count = sum(item["accepted_records"] for item in stats_by_district.values())
        report_md += (
            "\n## Latest Collection\n\n"
            f"- **Retrieved at:** {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
            f"- **Requested period:** {start_date[:4]}-{start_date[4:6]}-{start_date[6:]} "
            f"to {end_date[:4]}-{end_date[4:6]}-{end_date[6:]}\n"
            f"- **New source records parsed:** {fetched_record_count:,}\n"
            f"- **New source records within rainfall schema bounds:** {accepted_record_count:,}\n"
            f"- **Rainfall records quarantined by validation:** {len(rainfall_anomalies):,}\n"
            f"- **Districts retrieved:** {len(successful_locations)}\n"
            f"- **Rows in validated merged dataset:** {val_result.record_count:,}\n"
            f"- **Merged observation period:** {observation_start} to {observation_end}\n"
            f"- **Missing values by column in merged dataset:** "
            f"{json.dumps(val_result.missing_values_by_column, sort_keys=True)}\n"
            f"- **Raw response cache:** `data/raw/weather/`\n"
            "- **NASA POWER time standard:** provider default local solar time (LST).\n"
            "- **Requested parameters and canonical units:** PRECTOTCORR (mm/day), "
            "T2M_MIN (deg C), T2M_MAX (deg C), RH2M (%).\n"
        )
        report_md += (
            f"- **Provider time standard reported:** "
            f"{next((stats.get('time_standard') for stats in stats_by_district.values() if stats.get('time_standard')), 'Not reported')}.\n"
        )
        provider_version = next(
            (
                stats["parameter_metadata"].get("PRECTOTCORR", {}).get("longname")
                for stats in stats_by_district.values()
                if stats.get("parameter_metadata", {}).get("PRECTOTCORR")
            ),
            None,
        )
        if provider_version:
            report_md += f"- **PRECTOTCORR provider parameter:** {provider_version}.\n"
        api_version = next(
            (
                stats.get("provider_api_version")
                for stats in stats_by_district.values()
                if stats.get("provider_api_version")
            ),
            None,
        )
        if api_version:
            report_md += f"- **NASA POWER API version:** {api_version}.\n"
        provider_parameters = next(
            (
                stats.get("parameter_metadata")
                for stats in stats_by_district.values()
                if stats.get("parameter_metadata")
            ),
            {},
        )
        if provider_parameters:
            report_md += (
                f"- **Provider parameter metadata:** "
                f"`{json.dumps(provider_parameters, sort_keys=True)}`\n"
            )
        if anomaly_path:
            report_md += (
                f"- **Quarantine details:** `{anomaly_path.relative_to(self.data_dir).as_posix()}`; "
                "raw provider responses remain unchanged.\n"
            )
        report_md += (
            "\n| District | New records | Source | Missing PRECTOTCORR | "
            "Missing T2M_MIN | Missing T2M_MAX | Missing RH2M |\n"
            "|---|---:|---|---:|---:|---:|---:|\n"
        )
        for district in successful_locations:
            stats = stats_by_district[district]
            report_md += (
                f"| {district} | {stats['records']} | {stats['source']} | "
                f"{stats['missing_days']} | {stats['missing_tmin_days']} | "
                f"{stats['missing_tmax_days']} | {stats['missing_rh_days']} |\n"
            )
        if rainfall_anomalies:
            report_md += (
                "\n### Quarantined precipitation values\n\n"
                "| District | Date | Value | Unit | Reason |\n"
                "|---|---|---:|---|---|\n"
            )
            for anomaly in rainfall_anomalies:
                report_md += (
                    f"| {anomaly['district']} | {anomaly['date']} | "
                    f"{anomaly['rainfall_mm']} | {anomaly['unit']} | "
                    f"{anomaly['reason']} |\n"
                )

        quality_report_file = self.metadata_dir / "quality_report_weather.md"
        with open(quality_report_file, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"Data quality report saved to: {quality_report_file}")

        # Update Registry
        status = "ready_for_analysis" if val_result.is_valid else "validation_failed"
        self.registry.update_record("weather", {
            "status": status,
            "record_count": val_result.record_count,
            "processed_path": str(processed_csv).replace("\\", "/"),
            "observation_period": f"{observation_start} to {observation_end}",
            "geographic_coverage": "Kerala, India (14 districts)",
            "geographic_resolution": "0.5 x 0.5 degree gridded point reanalysis",
            "missing_value_count": val_result.missing_value_count,
            "missing_values_by_column": val_result.missing_values_by_column,
            "validation_status": "passed" if val_result.is_valid else "failed",
            "validation_summary": {
                "is_valid": val_result.is_valid,
                "record_count": val_result.record_count,
                "column_count": val_result.column_count,
                "missing_value_count": val_result.missing_value_count,
                "duplicate_record_count": val_result.duplicate_record_count,
                "districts_collected": len(successful_locations),
                "districts_failed": len(failed_locations),
                "new_source_records": fetched_record_count,
                "accepted_source_records": accepted_record_count,
                "quarantined_rainfall_records": len(rainfall_anomalies),
            },
            "processing_steps": [
                f"Retrieved {fetched_record_count:,} source records from NASA POWER daily point API (AG community) for {start_date} to {end_date}",
                "Raw responses archived in data/raw/weather/*.json",
                f"Merged and validated {len(all_records):,} daily observations across {len(successful_locations)} requested Kerala districts",
                f"Quarantined {len(rainfall_anomalies)} rainfall records outside the schema bounds; preserved the original values and raw responses",
                "Validated precipitation, humidity, and temperature ranges without clamping source values",
            ],
        })

        return {
            "success": val_result.is_valid,
            "total_records": len(all_records),
            "new_source_records": fetched_record_count,
            "accepted_source_records": accepted_record_count,
            "rainfall_anomaly_count": len(rainfall_anomalies),
            "anomaly_file": str(anomaly_path) if anomaly_path else None,
            "successful_locations": successful_locations,
            "failed_locations": failed_locations,
            "observation_period": f"{observation_start} to {observation_end}",
            "missing_values_by_column": val_result.missing_values_by_column,
            "validation": val_result.to_dict(),
            "processed_file": str(processed_csv),
            "report_file": str(quality_report_file),
        }


def main():
    parser = argparse.ArgumentParser(description="GROW Weather Ingestion Tool")
    parser.add_argument("--districts", nargs="+", help="Specific districts to ingest (default: all 14)")
    parser.add_argument("--start", default="20150101", help="Start date YYYYMMDD (default: 20150101)")
    parser.add_argument("--end", default="20251231", help="End date YYYYMMDD (default: 20251231)")
    parser.add_argument("--force", action="store_true", help="Force re-download even if cache exists")
    parser.add_argument("--pause", type=float, default=1.0, help="Pause seconds between API calls")

    args = parser.parse_args()

    collector = WeatherCollector()
    result = collector.run_ingestion(
        districts=args.districts,
        start_date=args.start,
        end_date=args.end,
        force_refresh=args.force,
        pause_between_calls=args.pause,
    )
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
