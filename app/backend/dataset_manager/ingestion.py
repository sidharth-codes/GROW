"""Dataset ingestion and manual upload staging service for GROW.

Handles safe file uploads, checksumming, raw archiving, schema validation,
and promotion to processed datasets without data loss or fabrication.
"""

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .schemas import DATASET_SCHEMAS, ValidationResult
from .validator import DatasetValidator
from .registry import DatasetRegistry


class DatasetIngestionService:
    """Manages file intake, safe staging, validation, and registry updates."""

    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit

    def __init__(
        self,
        base_data_dir: str = "data",
        registry: Optional[DatasetRegistry] = None,
        validator: Optional[DatasetValidator] = None,
    ):
        self.data_dir = Path(base_data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.derived_dir = self.data_dir / "derived"
        self.metadata_dir = self.data_dir / "metadata"

        for d in [self.raw_dir, self.processed_dir, self.derived_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.validator = validator or DatasetValidator()
        self.registry = registry or DatasetRegistry(
            metadata_dir=str(self.metadata_dir),
            validator=self.validator
        )

    def compute_sha256(self, file_path: str) -> str:
        """Compute SHA256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_manual_download_guidance(self, dataset_id: str) -> Dict[str, Any]:
        """Provide detailed manual download instructions and official source links."""
        schema = DATASET_SCHEMAS.get(dataset_id)
        if not schema:
            return {"error": f"Unknown dataset ID: {dataset_id}"}

        source = schema["source_info"]
        return {
            "dataset_id": dataset_id,
            "name": schema["name"],
            "organization": source.organization,
            "official_portal_url": source.source_url,
            "manual_page_url": source.manual_page_url or source.source_url,
            "download_method": source.download_method,
            "instructions": source.manual_export_instructions or "Export as CSV and upload through GROW portal.",
            "expected_filename": source.expected_filename,
            "expected_format": source.expected_format,
            "required_columns": [c.name for c in schema["columns"] if c.required],
            "all_columns": [c.name for c in schema["columns"]],
            "why_manual": (
                "Automated download is not possible due to portal session/CAPTCHA restrictions, "
                "dynamic JavaScript form submission, or lack of an open unauthenticated REST API endpoint."
                if source.download_method == "manual_upload" else "API download available."
            ),
        }

    def inspect_and_stage_upload(
        self, upload_file_path: str, dataset_id: str, original_filename: str
    ) -> Dict[str, Any]:
        """Pre-validation inspection before committing an uploaded file."""
        path = Path(upload_file_path)
        if not path.exists():
            return {
                "accepted": False,
                "error": f"Uploaded file not found at {upload_file_path}",
            }

        size = path.stat().st_size
        if size == 0:
            return {
                "accepted": False,
                "error": "Uploaded file is 0 bytes (empty). Please supply a file containing actual records.",
            }

        if size > self.MAX_FILE_SIZE_BYTES:
            return {
                "accepted": False,
                "error": f"File size ({size / 1024 / 1024:.1f} MB) exceeds maximum allowed (50 MB).",
            }

        if not (original_filename.lower().endswith(".csv") or path.suffix.lower() == ".csv"):
            return {
                "accepted": False,
                "error": "Only CSV (.csv) file formats are supported.",
            }

        checksum = self.compute_sha256(str(path))
        val_result = self.validator.validate_file(str(path), dataset_id)

        # Read sample rows for preview
        sample_rows = []
        headers = []
        try:
            import csv
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                for idx, row in enumerate(reader):
                    if idx >= 5:
                        break
                    sample_rows.append(row)
        except Exception as e:
            return {
                "accepted": False,
                "error": f"Could not parse CSV content: {e}",
            }

        return {
            "accepted": val_result.is_valid,
            "dataset_id": dataset_id,
            "original_filename": original_filename,
            "file_size_bytes": size,
            "sha256": checksum,
            "headers": headers,
            "sample_rows": sample_rows,
            "validation": val_result.to_dict(),
        }

    def commit_upload(
        self,
        staged_file_path: str,
        dataset_id: str,
        original_filename: str,
        source_note: str = "User manual upload",
    ) -> Dict[str, Any]:
        """Safely commit an accepted file to raw archive and processed directory."""
        staging_info = self.inspect_and_stage_upload(staged_file_path, dataset_id, original_filename)
        if not staging_info["accepted"]:
            return {
                "success": False,
                "error": "Validation failed. File was not committed.",
                "details": staging_info,
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_orig_name = Path(original_filename).name
        raw_target_name = f"{dataset_id}_{timestamp}_{safe_orig_name}"
        raw_target_path = self.raw_dir / raw_target_name

        # 1. Archive verbatim copy in data/raw/
        shutil.copy2(staged_file_path, raw_target_path)

        # 2. Promote to data/processed/<expected_filename>
        expected_filename = DATASET_SCHEMAS[dataset_id]["source_info"].expected_filename
        processed_target_path = self.processed_dir / expected_filename
        shutil.copy2(staged_file_path, processed_target_path)

        # 3. Maintain root data/<expected_filename> for backward compatibility
        root_target_path = self.data_dir / expected_filename
        shutil.copy2(staged_file_path, root_target_path)

        # 4. Generate data quality report
        val_result = self.validator.validate_file(str(processed_target_path), dataset_id)
        report_md = self.validator.generate_quality_report_markdown(
            dataset_id, str(processed_target_path), val_result
        )
        report_path = self.metadata_dir / f"quality_report_{dataset_id}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        # 5. Update registry
        self.registry.update_record(dataset_id, {
            "status": "ready_for_analysis",
            "record_count": val_result.record_count,
            "raw_path": str(raw_target_path).replace("\\", "/"),
            "processed_path": str(processed_target_path).replace("\\", "/"),
            "missing_value_count": val_result.missing_value_count,
            "missing_values_by_column": val_result.missing_values_by_column,
            "validation_status": "passed",
            "validation_summary": {
                "is_valid": True,
                "sha256": staging_info["sha256"],
                "record_count": val_result.record_count,
                "column_count": val_result.column_count,
                "missing_value_count": val_result.missing_value_count,
                "duplicate_record_count": val_result.duplicate_record_count,
                "quality_report": str(report_path).replace("\\", "/"),
            },
            "processing_steps": [
                f"Ingested from {safe_orig_name} via {source_note} at {datetime.now().isoformat()}",
                f"Archived raw copy to {raw_target_name}",
                f"Passed schema validation ({val_result.record_count} records)",
            ],
        })

        return {
            "success": True,
            "dataset_id": dataset_id,
            "records_committed": val_result.record_count,
            "raw_archive": str(raw_target_path),
            "processed_file": str(processed_target_path),
            "quality_report": str(report_path),
        }
