from pathlib import Path
from typing import Sequence

from tqdm import tqdm

from .load import load_enriched_data


def process_months(months: Sequence[str], data_dir: Path, debug: bool = False) -> None:
    """Main orchestration for aggregating SOTD data for one or more months."""
    for month in tqdm(months, desc="Aggregating months"):
        try:
            records = load_enriched_data(month, data_dir)
            # TODO: process records, aggregate, and save output
            if debug:
                print(f"Loaded {len(records)} records for {month}")
        except FileNotFoundError as e:
            print(f"[WARN] {e}")
        except Exception as e:
            print(f"[ERROR] Failed to process {month}: {e}")
