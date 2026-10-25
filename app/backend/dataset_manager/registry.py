"""Registry management for GROW agricultural datasets.

Stores and persists metadata, schemas, validation summaries, and provenance
records in data/metadata/dataset_registry.json.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .schemas import DATASET_SCHEMAS, DatasetMeta, DatasetSourceInfo
from .validator import DatasetValidator


class DatasetRegistry:
    """Manages dataset inventory, status lifecycle, and metadata persistence."""

    def __init__(
        self,
        metadata_dir: str = "data/metadata",
        registry_filename: str = "dataset_registry.json",
        validator: Optional[DatasetValidator] = None,
    ):
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.metadata_dir / registry_filename
        self.validator = validator or DatasetValidator()
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self._load_or_initialize()

    def _load_or_initialize(self) -> None:
        """Load registry from disk or initialize from schema definitions."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.datasets = json.load(f)
                    return
            except Exception:
                pass  # Fall back to initialization if corrupt

        # Initialize from DATASET_SCHEMAS
        self.datasets = {}
        for ds_id, schema in DATASET_SCHEMAS.items():
            source = schema["source_info"]
            columns_meta = []
            for col in schema["columns"]:
                columns_meta.append({
                    "name": col.name,
                    "dtype": col.dtype,
                    "required": col.required,
                    "description": col.description,
                    "unit": col.unit,
                    "min_value": col.min_value,
                    "max_value": col.max_value,
                })

            self.datasets[ds_id] = {
                "dataset_id": ds_id,
                "name": schema["name"],
                "category": schema["category"],
                "description": schema["description"],
                "status": "not_collected",
                "source_info": {
                    "organization": source.organization,
                    "source_url": source.source_url,
                    "download_method": source.download_method,
                    "api_endpoint": source.api_endpoint,
                    "manual_page_url": source.manual_page_url,
                    "manual_export_instructions": source.manual_export_instructions,
                    "expected_filename": source.expected_filename,
                    "expected_format": source.expected_format,
                    "license_or_terms": source.license_or_terms,
                },
                "geographic_coverage": "Kerala, India",
                "geographic_resolution": "District",
                "observation_period": "Not recorded",
                "record_count": 0,
                "column_count": len(columns_meta),
                "columns": columns_meta,
                "primary_key": schema.get("primary_key", []),
                "missing_value_count": 0,
                "missing_values_by_column": {},
                "last_updated": None,
                "raw_path": None,
                "processed_path": None,
                "validation_status": "unvalidated",
                "validation_summary": None,
                "data_quality_limitations": schema.get("limitations", []),
                "processing_steps": [],
            }
        self.save()

    def save(self) -> None:
        """Persist current registry state to JSON."""
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self.datasets, f, indent=2, ensure_ascii=False)

    def get(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        return self.datasets.get(dataset_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self.datasets.values())

    def update_record(self, dataset_id: str, updates: Dict[str, Any]) -> bool:
        if dataset_id not in self.datasets:
            return False
        self.datasets[dataset_id].update(updates)
        self.datasets[dataset_id]["last_updated"] = datetime.now().isoformat()
        self.save()
        return True

    def sync_with_existing_files(self, data_root: str = "data") -> Dict[str, Any]:
        """Audit the data directory, validate matching files, and update registry status."""
        root = Path(data_root)
        results = {}

        for ds_id, meta in self.datasets.items():
            expected_filename = meta["source_info"]["expected_filename"]
            target_path = root / expected_filename
            processed_path = root / "processed" / expected_filename

            # Check if file exists in data/processed or directly in data/
            actual_path = None
            if processed_path.exists() and processed_path.stat().st_size > 0:
                actual_path = processed_path
            elif target_path.exists() and target_path.stat().st_size > 0:
                actual_path = target_path

            if actual_path:
                val_result = self.validator.validate_file(str(actual_path), ds_id)
                status = "ready_for_analysis" if val_result.is_valid else "validation_failed"

                # Check if it has qualitative limitations
                if val_result.is_valid and ds_id in ["soil", "soil_crop_suitability_v2"]:
                    status = "partially_available"  # Valid heuristic/qualitative, not full lab measurements

                self.update_record(ds_id, {
                    "status": status,
                    "processed_path": str(actual_path).replace("\\", "/"),
                    "record_count": val_result.record_count,
                    "missing_value_count": val_result.missing_value_count,
                    "missing_values_by_column": val_result.missing_values_by_column,
                    "validation_status": "passed" if val_result.is_valid else "failed",
                    "validation_summary": {
                        "is_valid": val_result.is_valid,
                        "record_count": val_result.record_count,
                        "column_count": val_result.column_count,
                        "missing_value_count": val_result.missing_value_count,
                        "duplicate_record_count": val_result.duplicate_record_count,
                        "error_count": len(val_result.errors),
                        "warning_count": len(val_result.warnings),
                        "errors": val_result.errors[:5],
                        "warnings": val_result.warnings[:5],
                    },
                })
                results[ds_id] = {
                    "status": status,
                    "records": val_result.record_count,
                    "valid": val_result.is_valid,
                    "path": str(actual_path),
                }
            else:
                # File is missing or 0 bytes
                file_present_but_empty = target_path.exists() and target_path.stat().st_size == 0
                new_status = "awaiting_upload" if file_present_but_empty else "not_collected"
                self.update_record(ds_id, {
                    "status": new_status,
                    "record_count": 0,
                    "validation_status": "empty_file" if file_present_but_empty else "missing_file",
                })
                results[ds_id] = {
                    "status": new_status,
                    "records": 0,
                    "valid": False,
                    "path": str(target_path) if target_path.exists() else None,
                }

        return results
