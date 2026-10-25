"""Official agricultural statistics fetcher for Kerala.

Retrieves historical district-level crop area, production, and productivity
from the Department of Economics and Statistics (DES), Government of Kerala.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import requests

logger = logging.getLogger(__name__)

DES_KERALA_DATASET_URL = "https://ecostat.kerala.gov.in/dataset-download/28"


class DesKeralaYieldFetcher:
    """Fetches official DES Kerala agricultural statistics."""

    def __init__(self, raw_storage_dir: str = "data/raw/crop_yield"):
        self.raw_dir = Path(raw_storage_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.raw_file = self.raw_dir / "des_kerala_agriculture_statistics.csv"

    def fetch(self, force_download: bool = False, timeout_seconds: int = 30) -> Tuple[bool, Path, str]:
        """Fetch raw DES dataset or load from local cache.

        Returns:
            (success, file_path, source_message)
        """
        if not force_download and self.raw_file.exists() and self.raw_file.stat().st_size > 1000:
            return True, self.raw_file, f"Loaded from local cache ({self.raw_file.stat().st_size / 1024:.1f} KB)"

        headers = {
            "User-Agent": "GROW-Agri-Intelligence/1.0 (Kerala Agricultural Research; Python/requests)"
        }

        try:
            response = requests.get(DES_KERALA_DATASET_URL, headers=headers, timeout=timeout_seconds)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(self.raw_file, "wb") as f:
                    f.write(response.content)
                size_kb = len(response.content) / 1024
                return True, self.raw_file, f"Successfully downloaded from {DES_KERALA_DATASET_URL} ({size_kb:.1f} KB)"
            else:
                err = f"HTTP {response.status_code}: Unexpected response length {len(response.content)}"
                return False, self.raw_file, err
        except requests.exceptions.RequestException as re:
            err = f"Failed to download from DES Kerala: {str(re)}"
            if self.raw_file.exists():
                return True, self.raw_file, f"Network failed ({err}), fell back to existing cache"
            return False, self.raw_file, err
