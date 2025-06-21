#!/usr/bin/env python3
"""Annual comparison data loader for year-over-year delta calculations."""

import json
from pathlib import Path
from typing import Dict, List


class AnnualComparisonLoader:
    def __init__(self, debug: bool = False):
        self.debug = debug

    def load_comparison_years(self, years: List[str], data_dir: Path) -> Dict[str, dict]:
        """Load annual data for the given years from the specified directory.

        Args:
            years: List of years as strings (e.g., ["2023", "2022"])
            data_dir: Path to directory containing annual data files (e.g., 2023.json)

        Returns:
            Dict mapping year to loaded annual data (only for years successfully loaded)
        """
        results = {}
        for year in years:
            file_path = data_dir / f"{year}.json"
            if not file_path.exists():
                if self.debug:
                    print(f"[DEBUG] Missing annual file for year {year}")
                continue
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                if self.debug:
                    print(f"[DEBUG] Corrupted or invalid JSON for year {year}")
                continue
            if not isinstance(data, dict):
                if self.debug:
                    print(f"[DEBUG] Invalid structure for year {year} (not a dict)")
                continue
            results[year] = data
            if self.debug:
                print(f"[DEBUG] Loaded annual file for year {year}")
        return results
