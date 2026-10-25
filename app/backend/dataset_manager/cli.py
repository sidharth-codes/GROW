"""Command-line interface for the GROW Dataset Management module.

Allows auditing, validating, syncing, and staging dataset uploads directly
from the terminal or automation scripts.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.dataset_manager.schemas import DATASET_SCHEMAS
from app.backend.dataset_manager.registry import DatasetRegistry
from app.backend.dataset_manager.validator import DatasetValidator
from app.backend.dataset_manager.ingestion import DatasetIngestionService


def print_status_table(registry: DatasetRegistry) -> None:
    """Print an ASCII summary table of all managed datasets."""
    datasets = registry.list_all()
    print("\n" + "=" * 90)
    print(f"{'GROW DATASET INVENTORY REGISTRY':^90}")
    print("=" * 90)
    print(f"{'ID':<25} | {'Status':<18} | {'Records':<8} | {'Missing':<8} | {'Source Org':<22}")
    print("-" * 90)
    for d in datasets:
        ds_id = d["dataset_id"][:25]
        status = d["status"][:18]
        recs = str(d.get("record_count", 0))[:8]
        missing = str(d.get("missing_value_count", 0))[:8]
        org = d.get("source_info", {}).get("organization", "N/A")[:22]
        print(f"{ds_id:<25} | {status:<18} | {recs:<8} | {missing:<8} | {org:<22}")
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="GROW Dataset Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: list
    subparsers.add_parser("list", help="List all datasets and their statuses")

    # Command: sync
    subparsers.add_parser("sync", help="Scan data folder, validate files, and update registry")

    # Command: validate
    val_parser = subparsers.add_parser("validate", help="Validate a specific CSV file")
    val_parser.add_argument("dataset_id", help="Target dataset ID")
    val_parser.add_argument("file_path", help="Path to CSV file to validate")

    # Command: guide
    guide_parser = subparsers.add_parser("guide", help="Show manual download guidance for a dataset")
    guide_parser.add_argument("dataset_id", help="Target dataset ID")

    # Command: commit
    commit_parser = subparsers.add_parser("commit", help="Commit a validated file to the dataset registry")
    commit_parser.add_argument("dataset_id", help="Target dataset ID")
    commit_parser.add_argument("file_path", help="Path to source CSV file")

    args = parser.parse_args()

    service = DatasetIngestionService()
    registry = service.registry
    validator = service.validator

    if args.command == "list" or not args.command:
        print_status_table(registry)

    elif args.command == "sync":
        print("[*] Synchronizing dataset registry with existing data files...")
        results = registry.sync_with_existing_files("data")
        print("\nSync Results:")
        for ds_id, r in results.items():
            valid_flag = "VALID" if r["valid"] else "INVALID/EMPTY"
            print(f"  - {ds_id:<25}: Status={r['status']} ({r['records']} records, {valid_flag})")
        print_status_table(registry)

    elif args.command == "validate":
        print(f"[*] Validating '{args.file_path}' against schema '{args.dataset_id}'...")
        res = validator.validate_file(args.file_path, args.dataset_id)
        print(f"Result: {'PASS (Valid)' if res.is_valid else 'FAIL (Invalid)'}")
        print(f"Records: {res.record_count}, Columns: {res.column_count}")
        print(f"Missing Values: {res.missing_value_count}, Duplicates: {res.duplicate_record_count}")
        if res.errors:
            print("\nErrors:")
            for e in res.errors:
                print(f"  [X] {e}")
        if res.warnings:
            print("\nWarnings:")
            for w in res.warnings:
                print(f"  [!] {w}")

    elif args.command == "guide":
        guidance = service.get_manual_download_guidance(args.dataset_id)
        if "error" in guidance:
            print(f"Error: {guidance['error']}")
            return
        print(f"\n--- DATASET GUIDANCE: {guidance['name']} ({guidance['dataset_id']}) ---")
        print(f"Source Organization: {guidance['organization']}")
        print(f"Official Portal URL: {guidance['official_portal_url']}")
        print(f"Manual Page:        {guidance['manual_page_url']}")
        print(f"Why Manual:         {guidance['why_manual']}")
        print(f"Expected Filename:  {guidance['expected_filename']} ({guidance['expected_format']})")
        print(f"Instructions:\n  {guidance['instructions']}")
        print(f"Required Columns:\n  {', '.join(guidance['required_columns'])}")
        print(f"All Columns:\n  {', '.join(guidance['all_columns'])}\n")

    elif args.command == "commit":
        print(f"[*] Staging and committing '{args.file_path}' for '{args.dataset_id}'...")
        res = service.commit_upload(args.file_path, args.dataset_id, Path(args.file_path).name)
        if res["success"]:
            print(f"[OK] Successfully committed {res['records_committed']} records!")
            print(f"  Raw archive: {res['raw_archive']}")
            print(f"  Processed:   {res['processed_file']}")
            print(f"  Report:      {res['quality_report']}")
        else:
            print(f"[FAIL] Upload rejected: {res['error']}")
            if "details" in res and "validation" in res["details"]:
                for err in res["details"]["validation"].get("errors", []):
                    print(f"  [X] {err}")


if __name__ == "__main__":
    main()
