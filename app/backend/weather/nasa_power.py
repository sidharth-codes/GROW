"""NASA POWER API client for agro-meteorological data retrieval.

Retrieves daily precipitation (PRECTOTCORR), minimum temperature (T2M_MIN),
maximum temperature (T2M_MAX), and relative humidity (RH2M) for specified
coordinates and dates.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import requests


logger = logging.getLogger(__name__)

NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
MISSING_VALUE_SENTINEL = -999.0


class NasaPowerClient:
    """Client for querying the NASA POWER daily agroclimatology API."""

    def __init__(
        self,
        raw_storage_dir: str = "data/raw/weather",
        timeout_seconds: int = 45,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        self.raw_dir = Path(raw_storage_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GROW-Agri-Intelligence/1.0 (Kerala Agricultural Research; Python/requests)"
        })

    def get_cache_path(self, district: str, start_date: str, end_date: str) -> Path:
        """Construct raw cache filename for a district query."""
        safe_district = district.replace(" ", "_").lower()
        return self.raw_dir / f"nasa_power_{safe_district}_{start_date}_{end_date}.json"

    def fetch_district_daily(
        self,
        district: str,
        latitude: float,
        longitude: float,
        start_date: str,  # YYYYMMDD
        end_date: str,    # YYYYMMDD
        force_refresh: bool = False,
    ) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """Fetch daily meteorological data for a district.

        Returns:
            (success, list_of_daily_records, metadata_dict)
        """
        cache_path = self.get_cache_path(district, start_date, end_date)

        # Check local cache
        if not force_refresh and cache_path.exists() and cache_path.stat().st_size > 0:
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                records, meta = self._parse_nasa_response(raw_data, district, latitude, longitude)
                meta["source_type"] = "local_raw_cache"
                meta["cache_path"] = str(cache_path)
                return True, records, meta
            except Exception as e:
                logger.warning(f"Failed to read cache for {district}: {e}. Refetching from API.")

        # Prepare API parameters
        params = {
            "parameters": "PRECTOTCORR,T2M_MIN,T2M_MAX,RH2M",
            "community": "AG",
            "longitude": f"{longitude:.4f}",
            "latitude": f"{latitude:.4f}",
            "start": start_date,
            "end": end_date,
            "format": "JSON",
        }

        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    NASA_POWER_BASE_URL,
                    params=params,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    raw_json = response.json()

                    # Save verbatim raw response
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(raw_json, f, indent=2)

                    records, meta = self._parse_nasa_response(raw_json, district, latitude, longitude)
                    meta["source_type"] = "nasa_power_api"
                    meta["cache_path"] = str(cache_path)
                    return True, records, meta

                elif response.status_code in [429, 500, 502, 503, 504]:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    sleep_time = self.backoff_factor ** attempt
                    time.sleep(sleep_time)
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    break  # Client errors (4xx other than 429) do not retry

            except requests.exceptions.Timeout:
                last_error = f"Timeout ({self.timeout}s) connecting to NASA POWER."
                time.sleep(self.backoff_factor ** attempt)
            except requests.exceptions.ConnectionError as ce:
                last_error = f"Network connection error: {str(ce)}"
                time.sleep(self.backoff_factor ** attempt)
            except Exception as e:
                last_error = f"Unexpected request exception: {str(e)}"
                time.sleep(self.backoff_factor ** attempt)

        # Failure details
        meta = {
            "success": False,
            "district": district,
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "error": last_error,
            "manual_fallback_url": (
                f"https://power.larc.nasa.gov/data-access-viewer/?"
                f"lat={latitude}&lon={longitude}&start={start_date}&end={end_date}"
            ),
        }
        return False, [], meta

    def _parse_nasa_response(
        self,
        raw_json: Dict[str, Any],
        district: str,
        latitude: float,
        longitude: float
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Parse parameters dictionary from NASA POWER response."""
        props = raw_json.get("properties", {})
        param_dict = props.get("parameter", {})

        precip = param_dict.get("PRECTOTCORR", {})
        t_min = param_dict.get("T2M_MIN", {})
        t_max = param_dict.get("T2M_MAX", {})
        rh = param_dict.get("RH2M", {})

        # Collect sorted date keys
        all_dates = sorted(set(precip.keys()) | set(t_min.keys()) | set(t_max.keys()) | set(rh.keys()))

        records = []
        missing_precip = 0
        missing_tmin = 0
        missing_tmax = 0
        missing_rh = 0

        for d_str in all_dates:
            try:
                date_iso = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:]}"
            except Exception:
                continue

            r_val = precip.get(d_str)
            tmin_val = t_min.get(d_str)
            tmax_val = t_max.get(d_str)
            rh_val = rh.get(d_str)

            # Check sentinel values (-999.0)
            if r_val == MISSING_VALUE_SENTINEL or r_val is None:
                missing_precip += 1
                r_val = None
            else:
                r_val = max(0.0, float(r_val))  # Precipitation cannot be negative

            if tmin_val == MISSING_VALUE_SENTINEL or tmin_val is None:
                missing_tmin += 1
                tmin_val = None
            else:
                tmin_val = float(tmin_val)

            if tmax_val == MISSING_VALUE_SENTINEL or tmax_val is None:
                missing_tmax += 1
                tmax_val = None
            else:
                tmax_val = float(tmax_val)

            if rh_val == MISSING_VALUE_SENTINEL or rh_val is None:
                missing_rh += 1
                rh_val = None
            else:
                rh_val = min(100.0, max(0.0, float(rh_val)))

            # Only append record if values are present (no fabricated data)
            if all(v is not None for v in [r_val, tmin_val, tmax_val, rh_val]):
                records.append({
                    "district": district,
                    "date": date_iso,
                    "rainfall_mm": round(r_val, 2),
                    "temperature_min_c": round(tmin_val, 2),
                    "temperature_max_c": round(tmax_val, 2),
                    "humidity_percent": round(rh_val, 2),
                    "latitude": round(latitude, 4),
                    "longitude": round(longitude, 4),
                    "source": "NASA_POWER_AG_0.5DEG",
                })

        meta = {
            "success": True,
            "district": district,
            "latitude": latitude,
            "longitude": longitude,
            "total_dates_reported": len(all_dates),
            "valid_records_extracted": len(records),
            "missing_precipitation_days": missing_precip,
            "missing_tmin_days": missing_tmin,
            "missing_tmax_days": missing_tmax,
            "missing_rh_days": missing_rh,
        }
        return records, meta
