"""
Save extracted data to JSON files.

This module provides functions to save extraction results to JSON files
with consistent formatting and structure.
"""

from pathlib import Path

from sotd.utils.file_io import save_json_data


def save_month_file(month: str, result: dict, out_dir: Path = Path("data/extracted")) -> None:
    """
    Save the extraction result to a JSON file with the structure:
    {
        "meta": { ... },
        "data": [ ... ]
    }

    Parameters:
    - month: Month identifier in "YYYY-MM" format
    - result: Data to write to the file
    - out_dir: Directory where the file will be saved
    """
    out_path = out_dir / f"{month}.json"
    save_json_data(result, out_path, indent=2)
