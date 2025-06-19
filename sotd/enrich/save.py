"""
File I/O operations for the enrich phase.

Handles reading matched data and writing enriched data with comprehensive metadata.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def load_matched_data(file_path: Path) -> Optional[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    """
    Load matched data from a JSON file.

    Args:
        file_path: Path to the matched data file

    Returns:
        Tuple of (metadata, data) if file exists and is valid, None otherwise
    """
    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            content = json.load(f)

        if not isinstance(content, dict) or "data" not in content:
            return None

        metadata = content.get("meta", {})
        data = content.get("data", [])

        if not isinstance(data, list):
            return None

        return metadata, data

    except (json.JSONDecodeError, IOError):
        return None


def save_enriched_data(
    file_path: Path,
    enriched_data: List[Dict[str, Any]],
    original_metadata: Dict[str, Any],
    enrichment_stats: Dict[str, Any],
    force: bool = False,
) -> None:
    """
    Save enriched data to a JSON file with comprehensive metadata.

    Args:
        file_path: Path where to save the enriched data
        enriched_data: List of enriched comment records
        original_metadata: Metadata from the matched data
        enrichment_stats: Statistics about the enrichment process
        force: Whether to overwrite existing files
    """
    # Create output directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing file if force is True
    if force and file_path.exists():
        file_path.unlink()

    # Generate enrichment metadata
    enrichment_metadata = {
        "month": original_metadata.get("month", ""),
        "extracted_at": original_metadata.get("extracted_at", ""),
        "enriched_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "records_input": len(enriched_data),
        "record_count": len(enriched_data),
        "fields": ["razor", "blade", "soap", "brush"],
        **enrichment_stats,
    }

    # Prepare output structure
    output = {
        "data": enriched_data,
        "meta": enrichment_metadata,
    }

    # Write to file
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def calculate_enrichment_stats(enriched_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about the enrichment process.

    Args:
        enriched_data: List of enriched comment records

    Returns:
        Dictionary with enrichment statistics
    """
    stats = {
        "blade_enriched": 0,
        "razor_enriched": 0,
        "brush_enriched": 0,
        "soap_enriched": 0,
        "total_enriched": 0,
    }

    for comment in enriched_data:
        if "enriched" in comment:
            enriched = comment["enriched"]
            if "blade" in enriched:
                stats["blade_enriched"] += 1
            if "razor" in enriched:
                stats["razor_enriched"] += 1
            if "brush" in enriched:
                stats["brush_enriched"] += 1
            if "soap" in enriched:
                stats["soap_enriched"] += 1
            stats["total_enriched"] += 1

    return stats
