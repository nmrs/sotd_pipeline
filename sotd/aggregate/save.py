import json
from pathlib import Path
from typing import Any, Dict


def save_aggregated_data(data: Dict[str, Any], month: str, data_dir: Path) -> None:
    """Save aggregated data to JSON file with atomic write."""
    output_dir = data_dir / "aggregated"
    output_dir.mkdir(exist_ok=True)
    file_path = output_dir / f"{month}.json"

    # Create temporary file for atomic write
    temp_path = file_path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Atomic move
    temp_path.replace(file_path)


def generate_metadata(records: list[dict[str, Any]], month: str) -> Dict[str, Any]:
    """Generate metadata for aggregated data."""
    # TODO: implement metadata generation
    return {
        "month": month,
        "total_shaves": len(records),
        "unique_shavers": 0,  # TODO: calculate
        "avg_shaves_per_user": 0.0,  # TODO: calculate
    }
