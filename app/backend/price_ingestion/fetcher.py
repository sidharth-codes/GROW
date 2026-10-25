"""Market price data fetcher and manual fallback coordinator.

Coordinates automated attempts against official APIs (Data.gov.in / Agmarknet)
and provides detailed instructions, templates, and staging for user-supplied exports.
"""

import csv
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests

logger = logging.getLogger(__name__)


class AgmarknetPriceFetcher:
    """Handles Agmarknet / Data.gov.in mandi price acquisition."""

    DATA_GOV_IN_API_BASE = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    RESOURCE_TITLE = "Current Daily Price of Various Commodities from Various Markets (Mandi)"
    STATE_FILTER = "Keralam"
    PAGE_SIZE = 100
    MAX_PAGES = 100

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

        try:
            all_records = []
            raw_responses = []
            metadata = None
            expected_total = None
            offset = 0

            for _ in range(self.MAX_PAGES):
                params = {
                    "api-key": api_key,
                    "format": "json",
                    "filters[state]": self.STATE_FILTER,
                    "limit": self.PAGE_SIZE,
                    "offset": offset,
                }
                resp = requests.get(self.DATA_GOV_IN_API_BASE, params=params, timeout=20)
                if resp.status_code != 200:
                    detail = resp.text[:200].replace(api_key, "[REDACTED]")
                    return False, None, (
                        f"Data.gov.in responded with HTTP {resp.status_code}: {detail}"
                    )
                try:
                    payload = json.loads(resp.text)
                except json.JSONDecodeError as exc:
                    return False, None, f"Data.gov.in returned malformed JSON: {exc}"

                if not isinstance(payload, dict):
                    return False, None, "Data.gov.in returned an unexpected JSON response."
                if payload.get("error"):
                    detail = str(payload["error"]).replace(api_key, "[REDACTED]")
                    return False, None, f"Data.gov.in API error: {detail}"
                if payload.get("status") not in (None, "ok"):
                    message = str(payload.get("message", "unknown API status"))
                    message = message.replace(api_key, "[REDACTED]")
                    return False, None, f"Data.gov.in API status {payload['status']}: {message}"
                title = payload.get("title")
                if title and title != self.RESOURCE_TITLE:
                    return False, None, f"Unexpected Data.gov.in resource: {title}"

                records = payload.get("records")
                if not isinstance(records, list):
                    return False, None, "Data.gov.in response is missing its records list."
                if any(not isinstance(record, dict) for record in records):
                    return False, None, "Data.gov.in records contain malformed entries."

                try:
                    page_total = int(payload["total"]) if payload.get("total") is not None else None
                    page_count = int(payload["count"]) if payload.get("count") is not None else len(records)
                except (TypeError, ValueError):
                    return False, None, "Data.gov.in returned invalid pagination metadata."
                if page_total is not None and page_total < 0:
                    return False, None, "Data.gov.in returned an invalid total record count."
                if page_count != len(records):
                    return False, None, "Data.gov.in count does not match its records list."
                if len(records) > self.PAGE_SIZE:
                    return False, None, "Data.gov.in returned more records than the requested page size."
                if expected_total is None:
                    expected_total = page_total
                    metadata = {
                        key: payload.get(key)
                        for key in (
                            "title", "desc", "created_date", "updated_date",
                            "org", "source", "field",
                        )
                        if key in payload
                    }
                elif page_total is not None and page_total != expected_total:
                    return False, None, "Data.gov.in total changed while paginating."
                if payload.get("offset") is not None and int(payload["offset"]) != offset:
                    return False, None, "Data.gov.in returned an unexpected pagination offset."

                all_records.extend(records)
                raw_responses.append({
                    "offset": offset,
                    "body": resp.text.replace(api_key, "[REDACTED]"),
                })
                if not records:
                    break
                offset += len(records)
                if expected_total is not None:
                    if offset >= expected_total:
                        break
                    if offset > expected_total:
                        return False, None, "Data.gov.in returned more records than its total."
                elif len(records) < self.PAGE_SIZE:
                    break
            else:
                return False, None, "Data.gov.in pagination exceeded the maximum page count."

            if expected_total is not None and len(all_records) != expected_total:
                return False, None, (
                    f"Data.gov.in pagination returned {len(all_records)} records "
                    f"but reported {expected_total}."
                )
            if not all_records:
                return False, None, "Data.gov.in returned no market-price records."

            payload_to_save = {
                "title": (metadata or {}).get("title", self.RESOURCE_TITLE),
                "records": all_records,
                "_provenance": {
                    "endpoint": self.DATA_GOV_IN_API_BASE,
                    "resource_id": self.DATA_GOV_IN_API_BASE.rsplit("/", 1)[-1],
                    "query": {
                        "format": "json",
                        "filters[state]": self.STATE_FILTER,
                        "limit": self.PAGE_SIZE,
                    },
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "reported_total": expected_total,
                    "retrieved_count": len(all_records),
                    "page_count": len(raw_responses),
                    "resource_metadata": metadata or {},
                    "normalized_price_unit": None,
                    "source_price_unit": "UNVERIFIED",
                    "price_unit_status": "unverified",
                    "price_unit_field": "price_unit",
                    "price_unit_basis": (
                        "The API metadata does not provide a unit; raw numeric values "
                        "are preserved without conversion."
                    ),
                },
                "_raw_responses": raw_responses,
            }

            raw_path = self.raw_dir / "data_gov_in_kerala_prices.json"
            descriptor, temp_name = tempfile.mkstemp(
                prefix=".data_gov_in_kerala_prices.",
                suffix=".tmp",
                dir=self.raw_dir,
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as f:
                    json.dump(payload_to_save, f, ensure_ascii=False)
                os.replace(temp_name, raw_path)
            except OSError:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
                raise
            return True, raw_path, f"Successfully downloaded {len(all_records)} records from Data.gov.in API"
        except requests.RequestException as exc:
            return False, None, f"API connection failure: {type(exc).__name__}"
        except (OSError, TypeError, ValueError) as exc:
            return False, None, f"API response could not be saved or validated: {type(exc).__name__}"

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
