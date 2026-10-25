"""Market price ingestion pipeline for GROW.

Processes user-provided or API-sourced Agmarknet records, normalizes units,
validates schema, and generates data quality reports without fabricating missing records.
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.price_ingestion.fetcher import AgmarknetPriceFetcher
from app.backend.price_ingestion.normalizer import MarketPriceNormalizer
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

        self.fetcher = fetcher or AgmarknetPriceFetcher(raw_dir=str(self.raw_dir))
        self.normalizer = normalizer or MarketPriceNormalizer()
        self.validator = validator or DatasetValidator()
        self.registry = registry or DatasetRegistry(metadata_dir=str(self.metadata_dir))

    def run(self, input_file_path: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Run the market price ingestion pipeline."""
        print(f"\n{'='*80}")
        print("GROW MARKET PRICE INGESTION: AGMARKNET / DATA.GOV.IN")
        print(f"{'='*80}\n")

        source_file = None
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
        raw_rows = []
        with open(source_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for r in reader:
                raw_rows.append(r)

        normalized_records = []
        for r in raw_rows:
            norm = self.normalizer.normalize_record(r)
            if norm:
                normalized_records.append(norm)

        # Deduplicate
        seen = set()
        deduped = []
        for r in normalized_records:
            k = (r["date"], r["district"], r["market"], r["crop"], r["variety"])
            if k not in seen:
                seen.add(k)
                deduped.append(r)

        deduped.sort(key=lambda x: (x["date"], x["district"], x["crop"]))

        # Export to processed and root
        fieldnames = [
            "date", "district", "market", "crop", "variety",
            "min_price", "max_price", "modal_price", "price_unit", "source"
        ]
        processed_csv = self.processed_dir / "market_prices.csv"
        root_csv = self.data_dir / "market_prices.csv"

        for target in [processed_csv, root_csv]:
            with open(target, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(deduped)

        # Validate
        val_result = self.validator.validate_file(str(processed_csv), "market_prices")
        print(f"  Validation status: {'PASS (Valid)' if val_result.is_valid else 'FAIL (Errors)'}")

        # Quality report
        report_md = self.validator.generate_quality_report_markdown(
            "market_prices", str(processed_csv), val_result
        )
        report_file = self.metadata_dir / "quality_report_market_prices.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_md)

        status = "ready_for_analysis" if val_result.is_valid else "validation_failed"
        self.registry.update_record("market_prices", {
            "status": status,
            "record_count": val_result.record_count,
            "raw_path": str(source_file).replace("\\", "/"),
            "processed_path": str(processed_csv).replace("\\", "/"),
            "missing_value_count": val_result.missing_value_count,
            "missing_values_by_column": val_result.missing_values_by_column,
            "validation_status": "passed" if val_result.is_valid else "failed",
            "validation_summary": val_result.to_dict(),
        })

        return {
            "success": val_result.is_valid,
            "total_records": len(deduped),
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
