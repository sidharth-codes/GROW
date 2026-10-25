"""Price data normalizer for Kerala wholesale agricultural markets.

Standardizes trading dates, commodity taxonomy, market/district nomenclature,
and converts prices only when the source unit is known.
"""

import math
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
DISTRICT_ALIASES = {
    "kozhikode(calicut)": "Kozhikode",
    "palakad": "Palakkad",
    "thirssur": "Thrissur",
    "trivandrum": "Thiruvananthapuram",
}
UNVERIFIED_SOURCE_UNIT = "UNVERIFIED_SOURCE_UNIT"


class MarketPriceNormalizer:
    """Normalizes and validates agricultural price records."""

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """Convert varied date strings into ISO YYYY-MM-DD format."""
        date_str = str(date_str).strip()
        # Common formats in Agmarknet: DD/MM/YYYY, DD-Mon-YYYY, YYYY-MM-DD
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
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
        unit = re.sub(r"[^a-z]", "", raw_unit.lower())
        if unit in {
            "kg", "kilogram", "kilograms", "rskg", "inrkg",
            "rsperkg", "inrperkg",
        }:
            # Price per kg -> multiply by 100
            return round(price_val * 100.0, 2), "INR/quintal"
        if unit in {
            "tonne", "tonnes", "ton", "tons", "mt", "metricton",
            "metrictonne", "rsmt", "inrmt", "rspermt", "inrpermt",
        }:
            # Price per tonne -> divide by 10
            return round(price_val / 10.0, 2), "INR/quintal"
        if unit in {
            "", "q", "qt", "qtl", "quintal", "quintals",
            "rsquintal", "inrquintal", "rsqtl", "inqtl",
            "rsperquintal", "inrperquintal",
        }:
            return round(price_val, 2), "INR/quintal"
        raise ValueError(f"Unsupported price unit: {raw_unit}")

    def normalize_record(self, raw_row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a single market price record."""
        normalized_keys = {
            re.sub(r"[^a-z0-9]", "", str(key).lower()): value
            for key, value in raw_row.items()
        }

        def field(*names: str) -> Any:
            for name in names:
                value = normalized_keys.get(re.sub(r"[^a-z0-9]", "", name.lower()))
                if value is not None and str(value).strip():
                    return value
            return None

        # Find date field
        raw_date = field("date", "Price Date", "Arrival_Date", "arrival_date")
        if raw_date is None:
            return None
        norm_date = self.parse_date(raw_date)
        if not norm_date:
            return None

        raw_state = field("state", "State Name")
        if raw_state and str(raw_state).strip().casefold() not in {"kerala", "keralam", "kl"}:
            return None

        # Find district
        raw_district = field("district", "District Name")
        if raw_district is None:
            return None
        district_name = " ".join(str(raw_district).split()).lower()
        norm_district = DISTRICT_ALIASES.get(district_name)
        if not norm_district:
            norm_district = DISTRICT_MAPPING.get(district_name)
        if not norm_district:
            return None

        # Find market
        raw_market = field("market", "Market Name")
        if raw_market is None:
            return None
        norm_market = " ".join(str(raw_market).split())
        if not norm_market:
            return None

        # Find commodity
        raw_crop = field("crop", "Commodity", "crop_name")
        if raw_crop is None:
            return None
        crop_name = " ".join(str(raw_crop).split())
        norm_crop = COMMODITY_MAPPING.get(crop_name.casefold(), crop_name)
        if not norm_crop:
            return None

        raw_variety = field("variety", "Variety") or "Common"

        # Prices
        try:
            raw_min = field("min_price", "Min_Price")
            raw_max = field("max_price", "Max_Price")
            raw_modal = field("modal_price", "Modal_Price")
            if raw_min is None or raw_max is None or raw_modal is None:
                return None
            min_p = float(str(raw_min).replace(",", "").strip())
            max_p = float(str(raw_max).replace(",", "").strip())
            modal_p = float(str(raw_modal).replace(",", "").strip())
        except (TypeError, ValueError):
            return None

        if not all(math.isfinite(price) for price in (min_p, max_p, modal_p)):
            return None
        if min_p < 0 or min_p > max_p or not min_p <= modal_p <= max_p:
            return None

        raw_unit = field("price_unit", "Price_Unit", "unit")
        if raw_unit is None or str(raw_unit).strip().casefold() == UNVERIFIED_SOURCE_UNIT.casefold():
            norm_min, norm_max, norm_modal = min_p, max_p, modal_p
            norm_unit = UNVERIFIED_SOURCE_UNIT
        else:
            try:
                norm_min, norm_unit = self.normalize_price_to_quintal(min_p, str(raw_unit))
                norm_max, _ = self.normalize_price_to_quintal(max_p, str(raw_unit))
                norm_modal, _ = self.normalize_price_to_quintal(modal_p, str(raw_unit))
            except ValueError:
                return None

        raw_source = field("source")

        return {
            "date": norm_date,
            "district": norm_district,
            "market": norm_market,
            "crop": norm_crop,
            "variety": " ".join(str(raw_variety).split()),
            "min_price": norm_min,
            "max_price": norm_max,
            "modal_price": norm_modal,
            "price_unit": norm_unit,
            "source": str(raw_source).strip() if raw_source else "AGMARKNET_MANDI_BULLETIN",
        }
