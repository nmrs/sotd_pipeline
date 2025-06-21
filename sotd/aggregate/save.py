from pathlib import Path
from typing import Any, Dict

from sotd.utils.file_io import save_json_data


def save_aggregated_data(data: Dict[str, Any], month: str, data_dir: Path) -> None:
    """Save aggregated data to JSON file with atomic write."""
    output_dir = data_dir / "aggregated"
    output_dir.mkdir(exist_ok=True)
    file_path = output_dir / f"{month}.json"

    # Use unified file I/O utilities for atomic write
    save_json_data(data, file_path, indent=2)


def generate_metadata(records: list[dict[str, Any]], month: str) -> Dict[str, Any]:
    """Generate metadata for aggregated data."""
    # TODO: implement metadata generation
    return {
        "month": month,
        "total_shaves": len(records),
        "unique_shavers": 0,  # TODO: calculate
        "avg_shaves_per_user": 0.0,  # TODO: calculate
    }
