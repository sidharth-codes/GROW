"""Normalizer and processor for Kerala agricultural statistics.

Normalizes crop names, agricultural years, district names, units, and derives
crop yield per hectare following verified agricultural standards.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from app.backend.dataset_manager.schemas import KERALA_DISTRICTS

logger = logging.getLogger(__name__)

# Official mapping from DES Kerala crop nomenclature to GROW standard crops
CROP_NAME_MAPPING: Dict[str, str] = {
    "Paddy": "Rice",
    "Pepper": "Black pepper",
    "Coconut": "Coconut",
    "Banana": "Banana",
    "Rubber": "Rubber",
    "Tapioca": "Tapioca",
    "Ginger": "Ginger",
    "Turmeric": "Turmeric",
    "Plantain": "Plantain",
    "Cardamom": "Cardamom",
    "Cashew": "Cashew",
    "Arecanut": "Arecanut",
    "Coffee": "Coffee",
    "Tea": "Tea",
    "Cocoa": "Cocoa",
    "Nutmeg": "Nutmeg",
    "Cloves": "Cloves",
    "Pineapple": "Pineapple",
    "Pappaya": "Papaya",
    "Jack": "Jackfruit",
    "Mango": "Mango",
    "Betel leaves": "Betel leaves",
}

# Standard Kerala district spelling normalization
DISTRICT_NAME_MAPPING: Dict[str, str] = {d.lower(): d for d in KERALA_DISTRICTS}


class CropYieldProcessor:
    """Processes and standardizes raw agricultural statistics."""

    def process_raw_file(
        self,
        raw_csv_path: Path,
        filter_start_year: str = "2000-01",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Parse, normalize, and validate raw DES Kerala statistics.

        Args:
            raw_csv_path: Path to raw CSV file.
            filter_start_year: Optional start year filter (e.g. '2000-01' for modern 2000-2024 era).

        Returns:
            (list_of_clean_records, metrics_dict)
        """
        clean_records: List[Dict[str, Any]] = []
        raw_row_count = 0
        skipped_zero_area = 0
        skipped_invalid_values = 0
        skipped_unknown_district = 0
        skipped_prior_to_filter = 0
        derived_yield_count = 0

        crops_found = set()
        districts_found = set()
        years_found = set()

        with open(raw_csv_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_row_count += 1

                raw_year = (row.get("Agriculture Year") or "").strip()
                raw_district = (row.get("District") or "").strip()
                raw_crop = (row.get("Crop") or "").strip()
                raw_area = (row.get("Area") or "").strip()
                raw_prod = (row.get("Production") or "").strip()
                raw_prod_unit = (row.get("Production Unit") or "").strip()
                raw_productivity = (row.get("Productivity") or "").strip()

                # Filter by year if specified
                if filter_start_year and raw_year < filter_start_year:
                    skipped_prior_to_filter += 1
                    continue

                # Normalize district
                norm_district = DISTRICT_NAME_MAPPING.get(raw_district.lower())
                if not norm_district:
                    skipped_unknown_district += 1
                    continue

                # Normalize crop
                norm_crop = CROP_NAME_MAPPING.get(raw_crop, raw_crop)

                # Parse numerical area and production
                try:
                    area_ha = float(raw_area.replace(",", ""))
                    prod_val = float(raw_prod.replace(",", ""))
                except (ValueError, AttributeError):
                    skipped_invalid_values += 1
                    continue

                if area_ha <= 0 or prod_val < 0:
                    skipped_zero_area += 1
                    continue

                # Production unit handling
                # In DES Kerala, Coconut production is recorded in Million Nuts.
                # Average weight of dehusked coconut with water in Kerala is ~1.2 tonnes per 1,000 nuts (1.2 kg/nut).
                # 1 Million Nuts = 1,200 Metric Tonnes.
                if raw_prod_unit == "Million Nuts":
                    prod_tonnes = round(prod_val * 1200.0, 2)
                else:
                    prod_tonnes = round(prod_val, 2)

                # Productivity (Yield) handling
                yield_kg_ha = None
                try:
                    if raw_productivity and raw_productivity != "-":
                        parsed_prod = float(raw_productivity.replace(",", ""))
                        if parsed_prod > 0:
                            yield_kg_ha = parsed_prod
                except ValueError:
                    pass

                # Derive yield if missing or zero
                if not yield_kg_ha or yield_kg_ha <= 0:
                    yield_kg_ha = round((prod_tonnes * 1000.0) / area_ha, 2)
                    derived_yield_count += 1
                else:
                    yield_kg_ha = round(yield_kg_ha, 2)

                # Format agricultural year
                year_clean = raw_year

                clean_records.append({
                    "year": year_clean,
                    "district": norm_district,
                    "crop": norm_crop,
                    "season": "Annual",
                    "area_hectares": round(area_ha, 2),
                    "production_tonnes": prod_tonnes,
                    "yield_kg_per_hectare": yield_kg_ha,
                    "source": "DES_KERALA_ECOSTAT_28",
                })

                crops_found.add(norm_crop)
                districts_found.add(norm_district)
                years_found.add(year_clean)

        metrics = {
            "raw_row_count": raw_row_count,
            "retained_records": len(clean_records),
            "skipped_zero_area": skipped_zero_area,
            "skipped_invalid_values": skipped_invalid_values,
            "skipped_unknown_district": skipped_unknown_district,
            "skipped_prior_to_filter": skipped_prior_to_filter,
            "derived_yield_count": derived_yield_count,
            "distinct_crops": len(crops_found),
            "distinct_districts": len(districts_found),
            "distinct_years": len(years_found),
            "years_range": f"{min(years_found)} to {max(years_found)}" if years_found else "None",
        }
        return clean_records, metrics
