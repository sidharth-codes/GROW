"""Market price data fetcher and manual fallback coordinator.

Coordinates automated attempts against official APIs (Data.gov.in / Agmarknet)
and provides detailed instructions, templates, and staging for user-supplied exports.
"""

import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests

logger = logging.getLogger(__name__)


class AgmarknetPriceFetcher:
    """Handles Agmarknet / Data.gov.in mandi price acquisition."""

    DATA_GOV_IN_API_BASE = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    def __init__(self, raw_dir: str = "data/raw/market_prices"):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.template_file = self.raw_dir / "market_prices_template.csv"
        self._ensure_template()

    def _ensure_template(self) -> None:
        """Create an official CSV template file clearly labeled as a template."""
        if not self.template_file.exists():
            rows = [
                ["# TEMPLATE NOTICE: This is an upload template for GROW. Do not treat as historical data."],
                ["date", "district", "market", "crop", "variety", "min_price", "max_price", "modal_price", "price_unit", "source"],
                ["2023-01-05", "Palakkad", "Palakkad", "Rice", "Jyothi", "2050.00", "2200.00", "2150.00", "INR/quintal", "AGMARKNET_SAMPLE"],
                ["2023-01-05", "Kollam", "Kollam", "Coconut", "Cleaned", "2800.00", "3100.00", "3000.00", "INR/quintal", "AGMARKNET_SAMPLE"],
                ["2023-01-05", "Wayanad", "Kalpetta", "Black pepper", "Garbled", "48000.00", "51000.00", "49500.00", "INR/quintal", "AGMARKNET_SAMPLE"],
            ]
            with open(self.template_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

    def check_user_file_available(self) -> Optional[Path]:
        """Check if user has placed a CSV in the raw directory."""
        candidates = list(self.raw_dir.glob("*.csv"))
        # Exclude template file
        data_candidates = [c for c in candidates if "template" not in c.name.lower() and c.stat().st_size > 0]
        if data_candidates:
            # Return most recently modified candidate
            return max(data_candidates, key=lambda p: p.stat().st_mtime)
        return None

    def attempt_api_download(self, api_key: Optional[str] = None) -> Tuple[bool, Optional[Path], str]:
        """Attempt automated download from Data.gov.in / Agmarknet."""
        if not api_key:
            reason = (
                "Direct unauthenticated API download from Data.gov.in is restricted. "
                "Data.gov.in requires a registered user API key ('api-key' parameter), "
                "and the official Agmarknet portal (agmarknet.gov.in) enforces interactive ASP.NET "
                "session states with CAPTCHA protection for bulk historical downloads."
            )
            return False, None, reason

        # If API key is provided, query Data.gov.in
        params = {
            "api-key": api_key,
            "format": "json",
            "filters[state]": "Kerala",
            "limit": 5000,
        }
        try:
            resp = requests.get(self.DATA_GOV_IN_API_BASE, params=params, timeout=20)
            if resp.status_code == 200:
                raw_path = self.raw_dir / "data_gov_in_kerala_prices.json"
                with open(raw_path, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                return True, raw_path, "Successfully downloaded from Data.gov.in API"
            else:
                return False, None, f"Data.gov.in responded with HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            return False, None, f"API connection failure: {str(e)}"

    def get_manual_download_instructions(self) -> Dict[str, Any]:
        """Provide exact instructions for manual export from Agmarknet."""
        return {
            "source_name": "Agmarknet (Directorate of Marketing & Inspection, GoI)",
            "portal_url": "https://agmarknet.gov.in/",
            "direct_price_report_url": "https://agmarknet.gov.in/PriceTrends/SA_Pri_Month.aspx",
            "alternative_portal": "https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi",
            "steps": [
                "1. Open the Agmarknet Price Trends portal (https://agmarknet.gov.in/).",
                "2. Under 'State', select 'Kerala'.",
                "3. Select target commodities (Paddy, Coconut, Black pepper, Banana, Rubber, Tapioca, Ginger, Turmeric).",
                "4. Select the desired date range (e.g. 2015 to current).",
                "5. Click 'Submit' and export the resulting table to CSV / Excel.",
                "6. Save the exported CSV into: 'data/raw/market_prices/' as 'agmarknet_kerala_prices.csv', or upload via GROW UI.",
            ],
            "expected_fields": [
                "date", "district", "market", "crop", "variety",
                "min_price", "max_price", "modal_price", "price_unit"
            ],
            "template_path": str(self.template_file),
        }
