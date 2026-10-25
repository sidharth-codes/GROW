"""Pure-Python data validator for GROW agricultural datasets.

Enforces schema integrity, type validation, range bounds, categorical
consistency, primary key uniqueness, and missing value profiling without
external C-extension libraries.
"""

import csv
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .schemas import DATASET_SCHEMAS, ColumnDef, ValidationResult, ValidationIssue


class DatasetValidator:
    """Validates CSV datasets against formal schemas."""

    def __init__(self, schemas: Optional[Dict[str, Dict[str, Any]]] = None):
        self.schemas = schemas or DATASET_SCHEMAS

    def validate_file(self, file_path: str, dataset_id: str) -> ValidationResult:
        """Validate a CSV file against the specified dataset schema."""
        path = Path(file_path)
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                record_count=0,
                column_count=0,
                missing_value_count=0,
                missing_values_by_column={},
                duplicate_record_count=0,
                errors=[f"File does not exist: {file_path}"],
                warnings=[],
            )

        file_size = path.stat().st_size
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                record_count=0,
                column_count=0,
                missing_value_count=0,
                missing_values_by_column={},
                duplicate_record_count=0,
                errors=[f"File is completely empty (0 bytes): {file_path}"],
                warnings=[],
            )

        schema = self.schemas.get(dataset_id)
        if not schema:
            return ValidationResult(
                is_valid=False,
                record_count=0,
                column_count=0,
                missing_value_count=0,
                missing_values_by_column={},
                duplicate_record_count=0,
                errors=[f"Unknown dataset_id: {dataset_id}"],
                warnings=[],
            )

        col_defs: Dict[str, ColumnDef] = {col.name: col for col in schema["columns"]}
        required_cols = [c.name for c in schema["columns"] if c.required]
        primary_key_cols = schema.get("primary_key", [])

        errors: List[str] = []
        warnings: List[str] = []
        issues: List[ValidationIssue] = []
        missing_by_col: Dict[str, int] = {}
        seen_keys = set()
        duplicate_count = 0

        # Read CSV
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                try:
                    raw_headers = next(reader)
                except StopIteration:
                    return ValidationResult(
                        is_valid=False,
                        record_count=0,
                        column_count=0,
                        missing_value_count=0,
                        missing_values_by_column={},
                        duplicate_record_count=0,
                        errors=["File contains no rows (empty header)."],
                        warnings=[],
                    )

                # Strip whitespace and BOM
                headers = [h.strip().lstrip("\ufeff") for h in raw_headers]
                for h in headers:
                    missing_by_col[h] = 0

                # Validate headers
                missing_required = [c for c in required_cols if c not in headers]
                if missing_required:
                    errors.append(f"Missing required columns: {', '.join(missing_required)}")

                unexpected = [h for h in headers if h not in col_defs]
                if unexpected:
                    warnings.append(f"Unrecognized columns (ignored): {', '.join(unexpected)}")

                header_indices = {h: idx for idx, h in enumerate(headers)}
                total_missing = 0
                record_count = 0

                # Iterate rows
                for row_idx, row in enumerate(reader, start=2):
                    if not row or all(c.strip() == "" for c in row):
                        # Empty row
                        continue
                    record_count += 1

                    # Check row column length
                    if len(row) != len(headers):
                        issues.append(ValidationIssue(
                            level="ERROR",
                            row=row_idx,
                            column=None,
                            message=f"Row has {len(row)} values, expected {len(headers)} columns",
                        ))
                        continue

                    # Check primary key uniqueness
                    if primary_key_cols and all(pk in header_indices for pk in primary_key_cols):
                        key_vals = tuple(row[header_indices[pk]].strip() for pk in primary_key_cols)
                        if any(v == "" for v in key_vals):
                            issues.append(ValidationIssue(
                                level="ERROR",
                                row=row_idx,
                                column="primary_key",
                                message=f"Primary key contains blank value: {key_vals}",
                            ))
                        elif key_vals in seen_keys:
                            duplicate_count += 1
                            issues.append(ValidationIssue(
                                level="WARNING",
                                row=row_idx,
                                column="primary_key",
                                message=f"Duplicate primary key record: {key_vals}",
                            ))
                        else:
                            seen_keys.add(key_vals)

                    # Validate each column
                    for col_name, col_def in col_defs.items():
                        if col_name not in header_indices:
                            continue
                        col_idx = header_indices[col_name]
                        val_str = row[col_idx].strip() if col_idx < len(row) else ""

                        # Check blank
                        if val_str == "":
                            missing_by_col[col_name] = missing_by_col.get(col_name, 0) + 1
                            total_missing += 1
                            if col_def.required:
                                issues.append(ValidationIssue(
                                    level="ERROR",
                                    row=row_idx,
                                    column=col_name,
                                    message=f"Missing required value for '{col_name}'",
                                ))
                            continue

                        # Check dtype and constraints
                        issue = self._validate_cell_value(val_str, col_def, row_idx)
                        if issue:
                            issues.append(issue)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                record_count=0,
                column_count=0,
                missing_value_count=0,
                missing_values_by_column={},
                duplicate_record_count=0,
                errors=[f"Failed to read CSV file: {str(e)}"],
                warnings=[],
            )

        if record_count == 0:
            errors.append("Dataset has headers but 0 data records.")

        # Summarize issues
        err_issues = [i for i in issues if i.level == "ERROR"]
        warn_issues = [i for i in issues if i.level == "WARNING"]

        for i in err_issues[:15]:
            errors.append(f"Row {i.row}, col '{i.column}': {i.message}")
        if len(err_issues) > 15:
            errors.append(f"... and {len(err_issues) - 15} additional row validation errors.")

        for i in warn_issues[:10]:
            warnings.append(f"Row {i.row}, col '{i.column}': {i.message}")
        if len(warn_issues) > 10:
            warnings.append(f"... and {len(warn_issues) - 10} additional row warnings.")

        is_valid = len(errors) == 0

        details = [{
            "level": i.level,
            "row": i.row,
            "column": i.column,
            "message": i.message
        } for i in issues[:50]]

        return ValidationResult(
            is_valid=is_valid,
            record_count=record_count,
            column_count=len(headers),
            missing_value_count=total_missing,
            missing_values_by_column=missing_by_col,
            duplicate_record_count=duplicate_count,
            errors=errors,
            warnings=warnings,
            details=details,
        )

    def _validate_cell_value(self, val: str, col: ColumnDef, row_idx: int) -> Optional[ValidationIssue]:
        """Validate an individual cell value against its column definition."""
        dtype = col.dtype.lower()

        # Check allowed values
        if col.allowed_values and val not in col.allowed_values:
            # Check case-insensitive
            match = next((v for v in col.allowed_values if v.lower() == val.lower()), None)
            if not match:
                return ValidationIssue(
                    level="ERROR",
                    row=row_idx,
                    column=col.name,
                    message=f"Value '{val}' is not in allowed list: {col.allowed_values[:5]}...",
                )

        if dtype == "string":
            return None

        if dtype == "float":
            try:
                num = float(val)
                if col.min_value is not None and num < col.min_value:
                    return ValidationIssue(
                        level="ERROR",
                        row=row_idx,
                        column=col.name,
                        message=f"Value {num} is below minimum allowed {col.min_value}",
                    )
                if col.max_value is not None and num > col.max_value:
                    return ValidationIssue(
                        level="ERROR",
                        row=row_idx,
                        column=col.name,
                        message=f"Value {num} is above maximum allowed {col.max_value}",
                    )
            except ValueError:
                return ValidationIssue(
                    level="ERROR",
                    row=row_idx,
                    column=col.name,
                    message=f"Cannot parse '{val}' as floating point number",
                )

        elif dtype == "integer":
            try:
                num = int(float(val))
                if col.min_value is not None and num < col.min_value:
                    return ValidationIssue(
                        level="ERROR",
                        row=row_idx,
                        column=col.name,
                        message=f"Value {num} is below minimum allowed {col.min_value}",
                    )
                if col.max_value is not None and num > col.max_value:
                    return ValidationIssue(
                        level="ERROR",
                        row=row_idx,
                        column=col.name,
                        message=f"Value {num} is above maximum allowed {col.max_value}",
                    )
            except ValueError:
                return ValidationIssue(
                    level="ERROR",
                    row=row_idx,
                    column=col.name,
                    message=f"Cannot parse '{val}' as integer",
                )

        elif dtype == "date":
            # Match YYYY-MM-DD
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                return ValidationIssue(
                    level="ERROR",
                    row=row_idx,
                    column=col.name,
                    message=f"Invalid date '{val}', expected YYYY-MM-DD format",
                )

        elif dtype == "range":
            # e.g. "5.0-6.5" or "5.0 - 6.5"
            parts = re.split(r"\s*-\s*", val)
            if len(parts) == 2:
                try:
                    low = float(parts[0])
                    high = float(parts[1])
                    if low > high:
                        return ValidationIssue(
                            level="ERROR",
                            row=row_idx,
                            column=col.name,
                            message=f"Invalid range '{val}': lower bound ({low}) > upper bound ({high})",
                        )
                except ValueError:
                    return ValidationIssue(
                        level="ERROR",
                        row=row_idx,
                        column=col.name,
                        message=f"Cannot parse numeric range from '{val}'",
                    )
            else:
                return ValidationIssue(
                    level="WARNING",
                    row=row_idx,
                    column=col.name,
                    message=f"Expected numeric range formatted as 'min-max', found '{val}'",
                )

        return None

    def generate_quality_report_markdown(
        self, dataset_id: str, file_path: str, result: ValidationResult
    ) -> str:
        """Generate a structured Markdown data quality report."""
        schema = self.schemas.get(dataset_id, {})
        title = schema.get("name", dataset_id)

        lines = [
            f"# Data Quality Report: {title}",
            "",
            f"- **Dataset Identifier:** `{dataset_id}`",
            f"- **Target File:** `{file_path}`",
            f"- **Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Overall Status:** {'PASS (Valid)' if result.is_valid else 'FAIL (Errors Detected)'}",
            "",
            "## Summary Metrics",
            "",
            f"| Metric | Value |",
            f"| :--- | :--- |",
            f"| Total Records | {result.record_count} |",
            f"| Total Columns | {result.column_count} |",
            f"| Total Missing Values | {result.missing_value_count} |",
            f"| Duplicate Records | {result.duplicate_record_count} |",
            f"| Schema Compliance | {'100%' if result.is_valid else 'Non-compliant'} |",
            "",
            "## Missing Values by Column",
            "",
            "| Column | Missing Count | % Missing |",
            "| :--- | :--- | :--- |",
        ]

        for col, count in result.missing_values_by_column.items():
            pct = (count / result.record_count * 100) if result.record_count > 0 else 0
            lines.append(f"| `{col}` | {count} | {pct:.1f}% |")

        if result.errors:
            lines.extend([
                "",
                "## Validation Errors",
                "",
            ])
            for err in result.errors:
                lines.append(f"- :x: {err}")

        if result.warnings:
            lines.extend([
                "",
                "## Validation Warnings",
                "",
            ])
            for warn in result.warnings:
                lines.append(f"- :warning: {warn}")

        if schema.get("limitations"):
            lines.extend([
                "",
                "## Known Agricultural Data Limitations",
                "",
            ])
            for lim in schema["limitations"]:
                lines.append(f"- {lim}")

        return "\n".join(lines)
