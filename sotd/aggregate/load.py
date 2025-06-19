import json
from pathlib import Path
from typing import Any


def load_enriched_data(month: str, data_dir: Path) -> list[dict[str, Any]]:
    """Load enriched SOTD data for a given month from JSON file.
    Returns a list of enriched comment records.
    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if the file is malformed or missing required fields.
    """
    file_path = data_dir / "enriched" / f"{month}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Enriched data file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON in {file_path}: {e}")
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of records in {file_path}")
    # Basic validation: check for required fields in at least one record
    if data and not isinstance(data[0], dict):
        raise ValueError(f"Malformed record structure in {file_path}")
    return data
