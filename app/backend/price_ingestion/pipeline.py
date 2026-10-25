"""Market price ingestion pipeline for GROW.

Processes user-provided or API-sourced Agmarknet records, normalizes units,
validates schema, and generates data quality reports without fabricating missing records.
"""

import argparse
import csv
import io
import json
import logging
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.price_ingestion.fetcher import AgmarknetPriceFetcher
from app.backend.price_ingestion.normalizer import (
    MarketPriceNormalizer,
    UNVERIFIED_SOURCE_UNIT,
)
from app.backend.dataset_manager.validator import DatasetValidator
from app.backend.dataset_manager.registry import DatasetRegistry

logger = logging.getLogger("grow.price")


class MarketPriceIngestionPipeline:
    """Orchestrates market price ingestion, normalization, and quality reporting."""

    def __init__(
        self,
        base_data_dir: str = "data",
        fetcher: Optional[AgmarknetPriceFetcher] = None,
        normalizer: Optional[MarketPriceNormalizer] = None,
        validator: Optional[DatasetValidator] = None,
        registry: Optional[DatasetRegistry] = None,
    ):
        self.data_dir = Path(base_data_dir)
        self.raw_dir = self.data_dir / "raw" / "market_prices"
        self.processed_dir = self.data_dir / "processed"
        self.metadata_dir = self.data_dir / "metadata"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.fetcher = fetcher or AgmarknetPriceFetcher(raw_dir=str(self.raw_dir))
        self.normalizer = normalizer or MarketPriceNormalizer()
        self.validator = validator or DatasetValidator()
        self.registry = registry or DatasetRegistry(metadata_dir=str(self.metadata_dir))

    def run(self, input_file_path: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Run the market price ingestion pipeline."""
        if api_key is None:
            api_key = os.environ.get("DATA_GOV_IN_API_KEY")

        print(f"\n{'='*80}")
        print("GROW MARKET PRICE INGESTION: AGMARKNET / DATA.GOV.IN")
        print(f"{'='*80}\n")

        source_file = None
        api_error = None
        if input_file_path:
            p = Path(input_file_path)
            if p.exists() and p.stat().st_size > 0:
                source_file = p

        if not source_file:
            source_file = self.fetcher.check_user_file_available()

        if not source_file and api_key:
            print("[*] Attempting automated download via Data.gov.in API...", flush=True)
            success, raw_path, msg = self.fetcher.attempt_api_download(api_key=api_key)
            if success and raw_path:
                source_file = raw_path
            else:
                api_error = msg

        if api_error:
            return {
                "success": False,
                "status": "download_failed",
                "error": api_error,
            }

        # If no file is available, generate guidance and update registry as awaiting_upload
        if not source_file:
            print("[!] No user-provided historical price file detected in data/raw/market_prices/.")
            instructions = self.fetcher.get_manual_download_instructions()
            print(f"  - Official Portal:  {instructions['portal_url']}")
            print(f"  - Price Report:     {instructions['direct_price_report_url']}")
            print(f"  - Template Created: {instructions['template_path']}")
            print("\nDownload instructions for the user:")
            for s in instructions["steps"]:
                print(f"    {s}")

            # Generate data quality report explaining the pending state
            report_md = (
                "# Data Quality Report: Historical Agricultural Market Prices\n\n"
                "- **Dataset Identifier:** `market_prices`\n"
                f"- **Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "- **Status:** AWAITING USER UPLOAD\n\n"
                "## Collection Status and Diagnostics\n\n"
                "Automated ingestion from Data.gov.in requires a registered API key (`api-key`), "
                "and the official Agmarknet portal (agmarknet.gov.in) uses dynamic session state and CAPTCHAs "
                "which restrict headless unauthenticated bulk extraction.\n\n"
                "To maintain scientific integrity without fabricating synthetic prices, GROW requires "
                "an authentic export from Agmarknet or an API key.\n\n"
                "### Instructions to Provide Data:\n\n"
                f"1. Open [Agmarknet]({instructions['direct_price_report_url']})\n"
                "2. Filter: State = 'Kerala', select target crops, select date range\n"
                "3. Export to CSV\n"
                f"4. Place the file in `{self.raw_dir}/` or upload via the GROW UI.\n"
                f"5. An official CSV template is available at: `{instructions['template_path']}`\n"
            )

            report_file = self.metadata_dir / "quality_report_market_prices.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report_md)

            self.registry.update_record("market_prices", {
                "status": "awaiting_upload",
                "record_count": 0,
                "validation_status": "awaiting_user_upload",
                "validation_summary": {
                    "is_valid": False,
                    "record_count": 0,
                    "reason": "Automated download requires user API key or manual export from Agmarknet.",
                    "template_path": instructions["template_path"],
                },
                "processing_steps": [
                    "Created CSV template at data/raw/market_prices/market_prices_template.csv",
                    "Awaiting user-supplied official export from Agmarknet or Data.gov.in",
                ],
            })

            return {
                "success": False,
                "status": "awaiting_upload",
                "instructions": instructions,
                "report_file": str(report_file),
            }

        # If file is present, normalize and validate it
        print(f"[*] Processing market price file: {source_file}...", flush=True)
        try:
            if source_file.suffix.lower() == ".json":
                with open(source_file, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                if not isinstance(payload, dict):
                    raise ValueError("Expected a JSON object containing a records list")
                if payload.get("error"):
                    raise ValueError(f"Provider error: {payload['error']}")
                raw_rows = payload.get("records")
                if not isinstance(raw_rows, list):
                    raise ValueError("JSON response is missing its records list")
                if not raw_rows:
                    raise ValueError("Provider returned no market-price records")
                raw_rows = [
                    (
                        {
                            **row,
                            "source": row.get("source") or "DATA.GOV.IN_AGMARKNET_API",
                        }
                        if isinstance(row, dict)
                        else row
                    )
                    for row in raw_rows
                ]
            else:
                with open(source_file, "r", encoding="utf-8-sig", newline="") as f:
                    contents = f.read()
                if "# TEMPLATE NOTICE" in contents.upper():
                    raise ValueError("Template files are not authentic market observations")
                raw_rows = list(csv.DictReader(io.StringIO(contents)))
                if not raw_rows:
                    raise ValueError("Input file contains no market-price records")
            if not raw_rows:
                raise ValueError("Input contains no object-shaped market-price records")
        except (OSError, UnicodeError, json.JSONDecodeError, csv.Error, ValueError) as exc:
            return {
                "success": False,
                "status": "parse_failed",
                "error": f"Could not parse market-price input '{source_file}': {exc}",
            }

        normalized_records = []
        rejected_records = 0
        for row_idx, r in enumerate(raw_rows, start=2):
            if not isinstance(r, dict):
                rejected_records += 1
                continue
            source_value = next(
                (
                    str(value).strip()
                    for key, value in r.items()
                    if isinstance(key, str) and key.strip().casefold() == "source" and value
                ),
                "",
            )
            if "sample" in source_value.casefold():
                return {
                    "success": False,
                    "status": "parse_failed",
                    "error": (
                        f"Input file '{source_file}', row {row_idx} is marked as sample "
                        "data and cannot be ingested as an authentic observation."
                    ),
                }
            norm = self.normalizer.normalize_record(r)
            if not norm:
                rejected_records += 1
                continue
            normalized_records.append(norm)

        if not normalized_records:
            return {
                "success": False,
                "status": "normalization_failed",
                "error": f"Input file '{source_file}' contains no valid market-price records.",
                "records_retrieved": len(raw_rows),
                "valid_records": 0,
                "imported_records": 0,
                "duplicates_removed": 0,
                "rejected_records": rejected_records,
            }

        valid_record_count = len(normalized_records)
        fieldnames = [
            "date", "district", "market", "crop", "variety",
            "min_price", "max_price", "modal_price", "price_unit", "source"
        ]
        processed_csv = self.processed_dir / "market_prices.csv"
        root_csv = self.data_dir / "market_prices.csv"
        primary_key = ("date", "district", "market", "crop")
        duplicates_removed = 0
        input_duplicates_removed = 0
        existing_record_matches = 0
        records_updated = 0
        unique_records = {}
        for record in normalized_records:
            key = tuple(record[field] for field in primary_key)
            if key in unique_records:
                duplicates_removed += 1
                input_duplicates_removed += 1
            else:
                unique_records[key] = record

        combined_records = {}
        for existing_path in (root_csv, processed_csv):
            if not existing_path.exists() or existing_path.stat().st_size == 0:
                continue
            try:
                with open(existing_path, "r", encoding="utf-8-sig", newline="") as f:
                    existing_rows = list(csv.DictReader(f))
            except (OSError, UnicodeError, csv.Error) as exc:
                return {
                    "success": False,
                    "status": "existing_dataset_read_failed",
                    "error": f"Could not safely merge existing dataset '{existing_path}': {exc}",
                }
            for row_idx, row in enumerate(existing_rows, start=2):
                existing_record = self.normalizer.normalize_record(row)
                if not existing_record:
                    return {
                        "success": False,
                        "status": "existing_dataset_invalid",
                        "error": (
                            f"Existing dataset '{existing_path}', row {row_idx} is invalid; "
                            "it was not overwritten."
                        ),
                    }
                key = tuple(existing_record[field] for field in primary_key)
                if key in combined_records:
                    if existing_record != combined_records[key]:
                        return {
                            "success": False,
                            "status": "existing_dataset_conflict",
                            "error": (
                                f"Root and processed market-price datasets disagree "
                                f"on primary key {key}; neither was overwritten."
                            ),
                        }
                else:
                    combined_records[key] = existing_record

        imported_records = 0
        for key, record in unique_records.items():
            if key in combined_records:
                existing_record = combined_records[key]
                if (
                    record["price_unit"] == UNVERIFIED_SOURCE_UNIT
                    and existing_record["price_unit"] != UNVERIFIED_SOURCE_UNIT
                    and str(record.get("source", "")).startswith("DATA.GOV.IN")
                    and str(existing_record.get("source", "")).startswith("DATA.GOV.IN")
                ):
                    combined_records[key] = record
                    records_updated += 1
                duplicates_removed += 1
                existing_record_matches += 1
                continue
            combined_records[key] = record
            imported_records += 1

        normalized_records = sorted(
            combined_records.values(),
            key=lambda x: (x["date"], x["district"], x["market"], x["crop"]),
        )
        temp_files = []
        try:
            for target in (processed_csv, root_csv):
                descriptor, temp_name = tempfile.mkstemp(
                    prefix=f".{target.stem}.",
                    suffix=".csv",
                    dir=target.parent,
                )
                temp_files.append((Path(temp_name), target))
                with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(normalized_records)

            val_result = self.validator.validate_file(str(temp_files[0][0]), "market_prices")
            print(f"  Validation status: {'PASS (Valid)' if val_result.is_valid else 'FAIL (Errors)'}")
            if not val_result.is_valid:
                return {
                    "success": False,
                    "status": "validation_failed",
                    "error": "Normalized market-price records failed schema validation.",
                    "validation": val_result.to_dict(),
                }

            should_write = (
                imported_records > 0
                or records_updated > 0
                or not processed_csv.exists()
                or processed_csv.stat().st_size == 0
                or not root_csv.exists()
                or root_csv.stat().st_size == 0
            )
            if should_write:
                for temp_path, target in temp_files:
                    os.replace(temp_path, target)
                temp_files.clear()
        except OSError as exc:
            return {
                "success": False,
                "status": "save_failed",
                "error": f"Could not save validated market-price records: {exc}",
            }
        finally:
            for temp_path, _ in temp_files:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass

        # Quality report
        report_md = self.validator.generate_quality_report_markdown(
            "market_prices", str(processed_csv), val_result
        )
        report_file = self.metadata_dir / "quality_report_market_prices.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_md)

        status = "ready_for_analysis" if val_result.is_valid else "validation_failed"
        dates = [record["date"] for record in normalized_records]
        markets = sorted({record["market"] for record in normalized_records})
        commodities = sorted({record["crop"] for record in normalized_records})
        source_metadata = {}
        if source_file.suffix.lower() == ".json":
            source_metadata = payload.get("_provenance", {})
        registry_columns = self.registry.get("market_prices").get("columns", [])
        registry_columns = [
            {**column, "unit": None}
            if column.get("name") in {"min_price", "max_price", "modal_price"}
            else column
            for column in registry_columns
        ]
        self.registry.update_record("market_prices", {
            "status": status,
            "record_count": val_result.record_count,
            "raw_path": str(source_file).replace("\\", "/"),
            "processed_path": str(processed_csv).replace("\\", "/"),
            "missing_value_count": val_result.missing_value_count,
            "missing_values_by_column": val_result.missing_values_by_column,
            "validation_status": "passed" if val_result.is_valid else "failed",
            "validation_summary": val_result.to_dict(),
            "source_provenance": source_metadata,
            "columns": registry_columns,
        })

        return {
            "success": val_result.is_valid,
            "total_records": len(normalized_records),
            "records_retrieved": len(raw_rows),
            "valid_records": valid_record_count,
            "imported_records": imported_records,
            "input_duplicates_removed": input_duplicates_removed,
            "existing_record_matches": existing_record_matches,
            "records_updated": records_updated,
            "duplicates_removed": duplicates_removed,
            "rejected_records": rejected_records,
            "date_range": {"start": min(dates), "end": max(dates)},
            "markets": markets,
            "market_count": len(markets),
            "commodities": commodities,
            "commodity_count": len(commodities),
            "processed_file": str(processed_csv),
            "report_file": str(report_file),
        }


def main():
    parser = argparse.ArgumentParser(description="GROW Market Price Ingestion Pipeline")
    parser.add_argument("--file", help="Path to raw market price CSV file")
    parser.add_argument("--api-key", help="Data.gov.in API key")
    args = parser.parse_args()

    pipeline = MarketPriceIngestionPipeline()
    pipeline.run(input_file_path=args.file, api_key=args.api_key)


if __name__ == "__main__":
    main()
