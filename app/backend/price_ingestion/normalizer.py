"""Price data normalizer for Kerala wholesale agricultural markets.

Standardizes trading dates, commodity taxonomy, market/district nomenclature,
and converts diverse price units into standard INR/quintal.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from app.backend.dataset_manager.schemas import KERALA_DISTRICTS

# Commodity normalization mapping for Agmarknet / APMC mandis to GROW taxonomy
COMMODITY_MAPPING: Dict[str, str] = {
    "paddy": "Rice",
    "paddy(dhan)(common)": "Rice",
    "paddy(dhan)(basmati)": "Rice",
    "rice": "Rice",
    "coconut": "Coconut",
    "copra": "Coconut",
    "banana": "Banana",
    "banana - ripe": "Banana",
    "banana - green": "Banana",
    "banana(nendran)": "Banana",
    "banana(robusta)": "Banana",
    "black pepper": "Black pepper",
    "pepper": "Black pepper",
    "pepper garbled": "Black pepper",
    "pepper ungarbled": "Black pepper",
    "rubber": "Rubber",
    "rubber rss-4": "Rubber",
    "tapioca": "Tapioca",
    "cassava": "Tapioca",
    "ginger": "Ginger",
    "ginger(green)": "Ginger",
    "ginger(dry)": "Ginger",
    "turmeric": "Turmeric",
    "turmeric(raw)": "Turmeric",
    "turmeric(dry)": "Turmeric",
    "groundnut": "Groundnut",
    "groundnut pods": "Groundnut",
    "vegetables": "Vegetables",
    "bhindi(ladies finger)": "Vegetables",
    "bitter gourd": "Vegetables",
    "cowpea (veg)": "Vegetables",
    "cucumber": "Vegetables",
    "tomato": "Vegetables",
    "brinjal": "Vegetables",
    "arecanut": "Arecanut",
    "cardamom": "Cardamom",
    "cashew": "Cashew",
}

DISTRICT_MAPPING = {d.lower(): d for d in KERALA_DISTRICTS}


class MarketPriceNormalizer:
    """Normalizes and validates agricultural price records."""

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """Convert varied date strings into ISO YYYY-MM-DD format."""
        date_str = date_str.strip()
        # Common formats in Agmarknet: DD/MM/YYYY, DD-Mon-YYYY, YYYY-MM-DD
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @staticmethod
    def normalize_price_to_quintal(price_val: float, raw_unit: str) -> Tuple[float, str]:
        """Normalize price values to standard INR/quintal.

        1 Quintal = 100 Kilograms = 0.1 Metric Tonne.
        """
        unit = raw_unit.lower().strip()
        if "kg" in unit or "kilogram" in unit:
            # Price per kg -> multiply by 100
            return round(price_val * 100.0, 2), "INR/quintal"
        elif "tonne" in unit or "ton" in unit or "mt" in unit:
            # Price per tonne -> divide by 10
            return round(price_val / 10.0, 2), "INR/quintal"
        else:
            # Assume INR/quintal (Agmarknet standard)
            return round(price_val, 2), "INR/quintal"

    def normalize_record(self, raw_row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Normalize a single market price record."""
        # Find date field
        raw_date = raw_row.get("date") or raw_row.get("Price Date") or raw_row.get("Arrival_Date") or ""
        norm_date = self.parse_date(raw_date)
        if not norm_date:
            return None

        # Find district
        raw_district = raw_row.get("district") or raw_row.get("District") or raw_row.get("District Name") or ""
        norm_district = DISTRICT_MAPPING.get(raw_district.strip().lower())
        if not norm_district:
            return None

        # Find market
        raw_market = raw_row.get("market") or raw_row.get("Market") or raw_row.get("Market Name") or "Regulated Market"
        norm_market = raw_market.strip()

        # Find commodity
        raw_crop = raw_row.get("crop") or raw_row.get("Commodity") or raw_row.get("crop_name") or ""
        norm_crop = COMMODITY_MAPPING.get(raw_crop.strip().lower(), raw_crop.strip())

        raw_variety = raw_row.get("variety") or raw_row.get("Variety") or "Common"

        # Prices
        try:
            min_p = float(str(raw_row.get("min_price") or raw_row.get("Min_Price") or 0).replace(",", ""))
            max_p = float(str(raw_row.get("max_price") or raw_row.get("Max_Price") or 0).replace(",", ""))
            modal_p = float(str(raw_row.get("modal_price") or raw_row.get("Modal_Price") or 0).replace(",", ""))
        except ValueError:
            return None

        if modal_p <= 0 and min_p <= 0 and max_p <= 0:
            return None

        # If modal is zero but min/max exist, estimate modal as midpoint
        if modal_p <= 0:
            modal_p = (min_p + max_p) / 2.0
        if min_p <= 0:
            min_p = modal_p
        if max_p <= 0:
            max_p = modal_p

        # Sanity check: min <= modal <= max
        if min_p > max_p:
            min_p, max_p = max_p, min_p
        if modal_p < min_p:
            modal_p = min_p
        if modal_p > max_p:
            modal_p = max_p

        raw_unit = raw_row.get("price_unit") or raw_row.get("Price_Unit") or "INR/quintal"
        norm_min, norm_unit = self.normalize_price_to_quintal(min_p, raw_unit)
        norm_max, _ = self.normalize_price_to_quintal(max_p, raw_unit)
        norm_modal, _ = self.normalize_price_to_quintal(modal_p, raw_unit)

        return {
            "date": norm_date,
            "district": norm_district,
            "market": norm_market,
            "crop": norm_crop,
            "variety": raw_variety.strip(),
            "min_price": norm_min,
            "max_price": norm_max,
            "modal_price": norm_modal,
            "price_unit": norm_unit,
            "source": raw_row.get("source") or "AGMARKNET_MANDI_BULLETIN",
        }
