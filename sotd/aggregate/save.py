from datetime import datetime
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


def save_user_analysis_data(
    user_analyses: Dict[str, Dict[str, Any]], month: str, data_dir: Path
) -> None:
    """Save user analysis data to JSON file with atomic write."""
    output_dir = data_dir / "aggregated" / "user_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{month}.json"

    # Build output structure with metadata
    output_data = {
        "meta": {
            "month": month,
            "total_users": len(user_analyses),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
        "users": user_analyses,
    }

    # Use unified file I/O utilities for atomic write
    save_json_data(output_data, file_path, indent=2)


def save_product_usage_data(
    product_analyses: Dict[str, Dict[str, Dict[str, Any]]], month: str, data_dir: Path
) -> None:
    """Save product usage data to JSON file with atomic write."""
    output_dir = data_dir / "aggregated" / "product_usage"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{month}.json"

    # Build output structure with metadata
    output_data = {
        "meta": {
            "month": month,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
        **product_analyses,  # razors, blades, brushes, soaps
    }

    # Use unified file I/O utilities for atomic write
    save_json_data(output_data, file_path, indent=2)


def generate_metadata(records: list[dict[str, Any]], month: str) -> Dict[str, Any]:
    """Generate metadata for aggregated data."""
    # TODO: implement metadata generation
    return {
        "month": month,
        "total_shaves": len(records),
        "unique_shavers": 0,  # TODO: calculate
        "avg_shaves_per_user": 0.0,  # TODO: calculate
    }
