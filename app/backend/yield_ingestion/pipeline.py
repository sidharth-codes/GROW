"""Crop yield and production ingestion pipeline.

Executes download, normalization, deduplication, schema validation,
and registry persistence for historical Kerala crop statistics.
"""

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.yield_ingestion.fetcher import DesKeralaYieldFetcher
from app.backend.yield_ingestion.processor import CropYieldProcessor
from app.backend.dataset_manager.validator import DatasetValidator
from app.backend.dataset_manager.registry import DatasetRegistry

logger = logging.getLogger("grow.yield")


class CropYieldIngestionPipeline:
    """Orchestrates end-to-end ingestion of official Kerala crop statistics."""

    def __init__(
        self,
        base_data_dir: str = "data",
        fetcher: Optional[DesKeralaYieldFetcher] = None,
        processor: Optional[CropYieldProcessor] = None,
        validator: Optional[DatasetValidator] = None,
        registry: Optional[DatasetRegistry] = None,
    ):
        self.data_dir = Path(base_data_dir)
        self.raw_dir = self.data_dir / "raw" / "crop_yield"
        self.processed_dir = self.data_dir / "processed"
        self.metadata_dir = self.data_dir / "metadata"

        self.fetcher = fetcher or DesKeralaYieldFetcher(raw_storage_dir=str(self.raw_dir))
        self.processor = processor or CropYieldProcessor()
        self.validator = validator or DatasetValidator()
        self.registry = registry or DatasetRegistry(metadata_dir=str(self.metadata_dir))

    def run(self, force_download: bool = False, start_year: str = "2000-01") -> Dict[str, Any]:
        """Run the ingestion, normalization, and validation pipeline."""
        print(f"\n{'='*80}")
        print("GROW CROP YIELD INGESTION: DES KERALA (14 DISTRICTS)")
        print(f"{'='*80}\n")

        # 1. Fetch raw dataset
        print("[1/4] Fetching raw agricultural statistics from DES Kerala...", flush=True)
        success, raw_path, msg = self.fetcher.fetch(force_download=force_download)
        if not success:
            print(f"FAILED -> {msg}")
            return {
                "success": False,
                "error": msg,
            }
        print(f"  [OK] {msg}")

        # 2. Process and normalize records
        print(f"[2/4] Normalizing crop taxonomy, units, and agricultural years (from {start_year})...", flush=True)
        clean_records, metrics = self.processor.process_raw_file(raw_path, filter_start_year=start_year)
        print(f"  [OK] Retained {metrics['retained_records']:,} clean observations across {metrics['distinct_crops']} crops.")
        print(f"  - Districts covered: {metrics['distinct_districts']} / 14")
        print(f"  - Observation range: {metrics['years_range']}")
        print(f"  - Derived yields:     {metrics['derived_yield_count']}")

        # Deduplicate records by primary key: (year, district, crop, season)
        seen_keys = set()
        deduped_records = []
        for r in clean_records:
            k = (r["year"], r["district"], r["crop"], r["season"])
            if k not in seen_keys:
                seen_keys.add(k)
                deduped_records.append(r)

        # Sort chronologically by year, then district, then crop
        deduped_records.sort(key=lambda x: (x["year"], x["district"], x["crop"]))

        # 3. Export to processed and root CSV
        print("[3/4] Exporting standardized records to CSV...", flush=True)
        fieldnames = [
            "year",
            "district",
            "crop",
            "season",
            "area_hectares",
            "production_tonnes",
            "yield_kg_per_hectare",
            "source",
        ]
        processed_csv = self.processed_dir / "crop_yield.csv"
        root_csv = self.data_dir / "crop_yield.csv"

        for target in [processed_csv, root_csv]:
            with open(target, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(deduped_records)

        print(f"  [OK] Written {len(deduped_records):,} records to:")
        print(f"       - {processed_csv}")
        print(f"       - {root_csv}")

        # 4. Schema validation & quality report
        print("[4/4] Validating schema compliance and updating registry...", flush=True)
        val_result = self.validator.validate_file(str(processed_csv), "crop_yield")
        print(f"  Validation status: {'PASS (Valid)' if val_result.is_valid else 'FAIL (Errors)'}")
        if val_result.errors:
            for e in val_result.errors[:5]:
                print(f"  [X] {e}")

        # Generate Data Quality Report
        report_md = self.validator.generate_quality_report_markdown(
            "crop_yield", str(processed_csv), val_result
        )
        report_md += "\n\n## Agricultural Statistics Methodology\n\n"
        report_md += (
            "Statistics originate from the Department of Economics and Statistics (DES), Government of Kerala "
            "(Agricultural Statistics Portal dataset 28). The records reflect annual state agricultural censuses "
            "and crop-cutting experiments.\n\n"
            f"- **Observation Period:** {metrics['years_range']}\n"
            f"- **Total Districts:** {metrics['distinct_districts']} of 14 Kerala districts\n"
            f"- **Standardized Crops ({metrics['distinct_crops']}):** Rice (Paddy), Coconut, Banana, Black pepper, "
            "Rubber, Tapioca, Ginger, Turmeric, Arecanut, Cardamom, Cashew, Coffee, Tea, Plantain, etc.\n"
            "- **Units:** Area (Hectares), Production (Metric Tonnes), Yield (Kg/Hectare).\n"
            "- **Coconut Conversion:** Production reported in Million Nuts converted to equivalent metric tonnes (~1,200 MT per million nuts).\n"
        )

        quality_report_file = self.metadata_dir / "quality_report_crop_yield.md"
        with open(quality_report_file, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"  [OK] Quality report saved to: {quality_report_file}")

        # Update Registry
        status = "ready_for_analysis" if val_result.is_valid else "validation_failed"
        self.registry.update_record("crop_yield", {
            "status": status,
            "record_count": val_result.record_count,
            "raw_path": str(raw_path).replace("\\", "/"),
            "processed_path": str(processed_csv).replace("\\", "/"),
            "observation_period": metrics["years_range"],
            "geographic_coverage": "Kerala, India (14 districts)",
            "geographic_resolution": "District-level census",
            "missing_value_count": val_result.missing_value_count,
            "missing_values_by_column": val_result.missing_values_by_column,
            "validation_status": "passed" if val_result.is_valid else "failed",
            "validation_summary": {
                "is_valid": val_result.is_valid,
                "record_count": val_result.record_count,
                "column_count": val_result.column_count,
                "missing_value_count": val_result.missing_value_count,
                "duplicate_record_count": val_result.duplicate_record_count,
                "distinct_crops": metrics["distinct_crops"],
                "distinct_districts": metrics["distinct_districts"],
            },
            "processing_steps": [
                f"Ingested from DES Kerala portal (ecostat.kerala.gov.in/dataset/28) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "Raw copy preserved in data/raw/crop_yield/des_kerala_agriculture_statistics.csv",
                f"Normalized crop nomenclature (e.g. Paddy -> Rice, Pepper -> Black pepper)",
                f"Normalized area to hectares, production to MT, and derived yield kg/ha where missing",
                f"Retained {len(deduped_records):,} standardized observations ({metrics['years_range']})",
            ],
        })

        return {
            "success": val_result.is_valid,
            "total_records": len(deduped_records),
            "metrics": metrics,
            "processed_file": str(processed_csv),
            "report_file": str(quality_report_file),
        }


def main():
    parser = argparse.ArgumentParser(description="GROW Crop Yield Ingestion Pipeline")
    parser.add_argument("--force", action="store_true", help="Force re-download from DES Kerala")
    parser.add_argument("--start-year", default="2000-01", help="Starting agricultural year (default: 2000-01)")
    args = parser.parse_args()

    pipeline = CropYieldIngestionPipeline()
    pipeline.run(force_download=args.force, start_year=args.start_year)


if __name__ == "__main__":
    main()
