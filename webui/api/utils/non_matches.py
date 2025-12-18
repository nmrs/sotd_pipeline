#!/usr/bin/env python3
"""Shared utility module for managing non-matches files.

This module provides functions for loading and saving non-matches data
with support for recursive alphabetical sorting and atomic file writes.
"""

import copy
import logging
import os
from pathlib import Path
from typing import Any

import yaml

# Import normalization function from wsdb_alignment
from webui.api.wsdb_alignment import normalize_for_matching

logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_non_matches_dir() -> Path:
    """Get non-matches directory with SOTD_DATA_DIR support.

    Returns:
        Path to data/overrides/ directory
    """
    sotd_data_dir = os.environ.get("SOTD_DATA_DIR")
    if sotd_data_dir:
        return Path(sotd_data_dir) / "data" / "overrides"
    return PROJECT_ROOT / "data" / "overrides"


def _sort_brand_non_matches(data: dict[str, list[str]]) -> dict[str, list[str]]:
    """Sort brand non-matches data recursively.

    Args:
        data: Dict mapping brand -> list of non-match brands

    Returns:
        Sorted dict with sorted keys and sorted lists
    """
    sorted_data = {}
    for brand in sorted(data.keys()):
        sorted_data[brand] = sorted(data[brand])
    return sorted_data


def _sort_scent_non_matches(
    data: dict[str, dict[str, list[str]]],
) -> dict[str, dict[str, list[str]]]:
    """Sort scent non-matches data recursively.

    Args:
        data: Dict mapping brand -> scent -> list of non-match scents

    Returns:
        Sorted dict with all keys and lists sorted alphabetically
    """
    sorted_data = {}
    for brand in sorted(data.keys()):
        sorted_data[brand] = {}
        for scent in sorted(data[brand].keys()):
            sorted_data[brand][scent] = sorted(data[brand][scent])
    return sorted_data


def _sort_cross_brand_scent_non_matches(
    data: dict[str, list[dict[str, str]]],
) -> dict[str, list[dict[str, str]]]:
    """Sort cross-brand scent non-matches data recursively.

    Args:
        data: Dict mapping scent_name -> list of {brand, scent} dicts

    Returns:
        Sorted dict with sorted keys and sorted lists (by brand name)
    """
    sorted_data = {}
    for scent_name in sorted(data.keys()):
        # Sort the list of brand-scent pairs by brand name
        sorted_pairs = sorted(
            data[scent_name], key=lambda x: (x.get("brand", "").lower(), x.get("scent", "").lower())
        )
        sorted_data[scent_name] = sorted_pairs
    return sorted_data


def _sort_non_matches_data(data: dict, file_type: str) -> dict:
    """Recursively sort non-matches data based on file type.

    Args:
        data: The data to sort
        file_type: One of "brands", "scents", or "scents_cross_brand"

    Returns:
        Sorted data with all keys and nested values sorted alphabetically
    """
    if file_type == "brands":
        return _sort_brand_non_matches(data)
    elif file_type == "scents":
        return _sort_scent_non_matches(data)
    elif file_type == "scents_cross_brand":
        return _sort_cross_brand_scent_non_matches(data)
    else:
        logger.warning(f"Unknown file type for sorting: {file_type}, returning unsorted data")
        return data


def _enforce_brand_symmetry(brand_non_matches: dict[str, list[str]]) -> dict[str, list[str]]:
    """Ensure all brand non-matches are stored symmetrically.

    If A has B in its list, ensure B also has A in its list.

    Args:
        brand_non_matches: Dict mapping brand -> list of non-match brands

    Returns:
        Symmetrized dict with all relationships stored both ways
    """
    # Create a copy to avoid modifying during iteration
    result = {brand: list(non_matches) for brand, non_matches in brand_non_matches.items()}

    # For each brand and its non-matches, ensure reverse relationships exist
    for brand, non_matches in brand_non_matches.items():
        for non_match in non_matches:
            # Ensure reverse relationship exists
            if non_match not in result:
                result[non_match] = []
            if brand not in result[non_match]:
                result[non_match].append(brand)

    return result


def _enforce_scent_symmetry(
    scent_non_matches: dict[str, dict[str, list[str]]],
) -> dict[str, dict[str, list[str]]]:
    """Ensure all scent non-matches are stored symmetrically.

    If brand X has scent A with B in its list, ensure scent B also has A in its list.

    Args:
        scent_non_matches: Dict mapping brand -> scent -> list of non-match scents

    Returns:
        Symmetrized dict with all relationships stored both ways
    """
    # Create a copy to avoid modifying during iteration
    result = {}
    for brand in scent_non_matches:
        result[brand] = {
            scent: list(non_matches) for scent, non_matches in scent_non_matches[brand].items()
        }

    # For each brand-scent combination and its non-matches, ensure reverse relationships exist
    for brand, scents in scent_non_matches.items():
        for scent, non_matches in scents.items():
            for non_match in non_matches:
                # Ensure reverse relationship exists
                if brand not in result:
                    result[brand] = {}
                if non_match not in result[brand]:
                    result[brand][non_match] = []
                if scent not in result[brand][non_match]:
                    result[brand][non_match].append(scent)

    return result


def _atomic_write_yaml(file_path: Path, data: dict, file_type: str) -> None:
    """Write YAML file atomically with recursive alphabetical sorting.

    Args:
        file_path: Path to the YAML file
        data: Data to write
        file_type: Type of file for sorting ("brands", "scents", or "scents_cross_brand")
    """
    # Sort data recursively
    sorted_data = _sort_non_matches_data(data, file_type)

    # Write to temporary file first
    temp_file = file_path.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as f:
        yaml.dump(
            sorted_data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=True,  # Additional top-level key sorting
        )
    # Atomic replace
    temp_file.replace(file_path)


def load_non_matches() -> dict[str, Any]:
    """Load all non-match files.

    Returns:
        Dict with keys:
        - brand_non_matches: dict[str, list[str]]
        - scent_non_matches: dict[str, dict[str, list[str]]]
        - scent_cross_brand_non_matches: dict[str, list[dict]]
    """
    try:
        logger.info("📂 Loading known non-matches")
        overrides_dir = get_non_matches_dir()
        brands_file = overrides_dir / "non_matches_brands.yaml"
        scents_file = overrides_dir / "non_matches_scents.yaml"
        scents_cross_brand_file = overrides_dir / "non_matches_scents_cross_brand.yaml"

        # Load brand non-matches
        brand_non_matches = {}
        if brands_file.exists():
            with brands_file.open("r", encoding="utf-8") as f:
                brand_non_matches = yaml.safe_load(f) or {}

        # Load scent non-matches (same-brand)
        scent_non_matches = {}
        if scents_file.exists():
            with scents_file.open("r", encoding="utf-8") as f:
                scent_non_matches = yaml.safe_load(f) or {}

        # Load cross-brand scent non-matches
        scent_cross_brand_non_matches = {}
        if scents_cross_brand_file.exists():
            with scents_cross_brand_file.open("r", encoding="utf-8") as f:
                scent_cross_brand_non_matches = yaml.safe_load(f) or {}

        # Store original data to detect changes
        original_brand_non_matches = copy.deepcopy(brand_non_matches)
        original_scent_non_matches = copy.deepcopy(scent_non_matches)

        # Enforce symmetry on loaded data (fixes any manually edited asymmetric entries)
        brand_non_matches = _enforce_brand_symmetry(brand_non_matches)
        scent_non_matches = _enforce_scent_symmetry(scent_non_matches)

        # If symmetry enforcement added entries, save the fixed data back
        # (This ensures manual edits are automatically fixed on next load)
        if brand_non_matches != original_brand_non_matches:
            _atomic_write_yaml(brands_file, brand_non_matches, "brands")
            logger.info("🔧 Fixed asymmetric brand non-matches and saved")

        if scent_non_matches != original_scent_non_matches:
            _atomic_write_yaml(scents_file, scent_non_matches, "scents")
            logger.info("🔧 Fixed asymmetric scent non-matches and saved")

        brand_count = sum(len(v) for v in brand_non_matches.values())
        scent_count = sum(
            len(scents)
            for brand_scents in scent_non_matches.values()
            for scents in brand_scents.values()
        )
        cross_brand_count = sum(len(pairs) for pairs in scent_cross_brand_non_matches.values())

        logger.info(
            f"✅ Loaded {brand_count} brand non-matches, {scent_count} scent non-matches, {cross_brand_count} cross-brand scent non-matches"
        )

        return {
            "brand_non_matches": brand_non_matches,
            "scent_non_matches": scent_non_matches,
            "scent_cross_brand_non_matches": scent_cross_brand_non_matches,
        }

    except Exception as e:
        logger.error(f"❌ Failed to load non-matches: {e}")
        raise


def save_brand_non_match(pipeline_brand: str, wsdb_brand: str) -> dict[str, Any]:
    """Save brand non-match with duplicate checking.

    Args:
        pipeline_brand: Pipeline brand name
        wsdb_brand: WSDB brand name that doesn't match

    Returns:
        Dict with 'success' and 'message' keys
    """
    try:
        logger.info(f"➕ Adding brand non-match: {pipeline_brand} != {wsdb_brand}")

        overrides_dir = get_non_matches_dir()
        overrides_dir.mkdir(parents=True, exist_ok=True)
        brands_file = overrides_dir / "non_matches_brands.yaml"

        # Load existing data
        brand_non_matches = {}
        if brands_file.exists():
            with brands_file.open("r", encoding="utf-8") as f:
                brand_non_matches = yaml.safe_load(f) or {}

        # Add non-match in both directions
        if pipeline_brand not in brand_non_matches:
            brand_non_matches[pipeline_brand] = []
        if wsdb_brand not in brand_non_matches:
            brand_non_matches[wsdb_brand] = []

        # Check for duplicate
        if wsdb_brand in brand_non_matches[pipeline_brand]:
            logger.info("ℹ️ Non-match already exists, skipping")
            return {"success": True, "message": "Non-match already exists"}

        # Add both directions
        brand_non_matches[pipeline_brand].append(wsdb_brand)
        if pipeline_brand not in brand_non_matches[wsdb_brand]:
            brand_non_matches[wsdb_brand].append(pipeline_brand)

        # Enforce symmetry (handles any edge cases)
        brand_non_matches = _enforce_brand_symmetry(brand_non_matches)

        # Save atomically with sorting
        _atomic_write_yaml(brands_file, brand_non_matches, "brands")

        logger.info("✅ Brand non-match added and saved successfully")
        return {"success": True, "message": "Brand non-match added successfully"}

    except Exception as e:
        logger.error(f"❌ Failed to add brand non-match: {e}")
        raise


def save_scent_non_match(
    pipeline_brand: str, pipeline_scent: str, wsdb_scent: str
) -> dict[str, Any]:
    """Save same-brand scent non-match with duplicate checking.

    Args:
        pipeline_brand: Pipeline brand name
        pipeline_scent: Pipeline scent name
        wsdb_scent: WSDB scent name that doesn't match

    Returns:
        Dict with 'success' and 'message' keys
    """
    try:
        logger.info(
            f"➕ Adding scent non-match: {pipeline_brand} - {pipeline_scent} != {wsdb_scent}"
        )

        overrides_dir = get_non_matches_dir()
        overrides_dir.mkdir(parents=True, exist_ok=True)
        scents_file = overrides_dir / "non_matches_scents.yaml"

        # Load existing data
        scent_non_matches = {}
        if scents_file.exists():
            with scents_file.open("r", encoding="utf-8") as f:
                scent_non_matches = yaml.safe_load(f) or {}

        # Add non-match in both directions
        if pipeline_brand not in scent_non_matches:
            scent_non_matches[pipeline_brand] = {}
        if pipeline_scent not in scent_non_matches[pipeline_brand]:
            scent_non_matches[pipeline_brand][pipeline_scent] = []
        if wsdb_scent not in scent_non_matches[pipeline_brand]:
            scent_non_matches[pipeline_brand][wsdb_scent] = []

        # Check for duplicate
        if wsdb_scent in scent_non_matches[pipeline_brand][pipeline_scent]:
            logger.info("ℹ️ Non-match already exists, skipping")
            return {"success": True, "message": "Non-match already exists"}

        # Add both directions
        scent_non_matches[pipeline_brand][pipeline_scent].append(wsdb_scent)
        if pipeline_scent not in scent_non_matches[pipeline_brand][wsdb_scent]:
            scent_non_matches[pipeline_brand][wsdb_scent].append(pipeline_scent)

        # Enforce symmetry (handles any edge cases)
        scent_non_matches = _enforce_scent_symmetry(scent_non_matches)

        # Save atomically with sorting
        _atomic_write_yaml(scents_file, scent_non_matches, "scents")

        logger.info("✅ Scent non-match added and saved successfully")
        return {"success": True, "message": "Scent non-match added successfully"}

    except Exception as e:
        logger.error(f"❌ Failed to add scent non-match: {e}")
        raise


def save_cross_brand_scent_non_match(
    entry1_brand: str, entry1_scent: str, entry2_brand: str, entry2_scent: str
) -> dict[str, Any]:
    """Save cross-brand scent non-match with duplicate checking.

    Args:
        entry1_brand: First entry brand name
        entry1_scent: First entry scent name
        entry2_brand: Second entry brand name
        entry2_scent: Second entry scent name

    Returns:
        Dict with 'success' and 'message' keys
    """
    try:
        logger.info(
            f"➕ Adding cross-brand scent non-match: {entry1_brand} - {entry1_scent} != {entry2_brand} - {entry2_scent}"
        )

        # Normalize for comparison
        brand1_norm = normalize_for_matching(entry1_brand)
        brand2_norm = normalize_for_matching(entry2_brand)
        scent1_norm = normalize_for_matching(entry1_scent)
        scent2_norm = normalize_for_matching(entry2_scent)

        overrides_dir = get_non_matches_dir()
        overrides_dir.mkdir(parents=True, exist_ok=True)
        scents_cross_brand_file = overrides_dir / "non_matches_scents_cross_brand.yaml"

        # Load existing data
        scent_cross_brand_non_matches = {}
        if scents_cross_brand_file.exists():
            with scents_cross_brand_file.open("r", encoding="utf-8") as f:
                scent_cross_brand_non_matches = yaml.safe_load(f) or {}

        # Use the normalized scent name as the key (use entry1_scent as the canonical name)
        scent_key = entry1_scent

        # Initialize if needed
        if scent_key not in scent_cross_brand_non_matches:
            scent_cross_brand_non_matches[scent_key] = []

        # Create brand-scent pairs for both entries
        entry1_pair = {"brand": entry1_brand, "scent": entry1_scent}
        entry2_pair = {"brand": entry2_brand, "scent": entry2_scent}

        # Check if entry1 is already in the group
        entry1_exists = any(
            normalize_for_matching(pair.get("brand", "")) == brand1_norm
            and normalize_for_matching(pair.get("scent", "")) == scent1_norm
            for pair in scent_cross_brand_non_matches[scent_key]
        )

        # Check if entry2 is already in the group
        entry2_exists = any(
            normalize_for_matching(pair.get("brand", "")) == brand2_norm
            and normalize_for_matching(pair.get("scent", "")) == scent2_norm
            for pair in scent_cross_brand_non_matches[scent_key]
        )

        # If both exist, they're already marked as non-matches
        if entry1_exists and entry2_exists:
            logger.info("ℹ️ Non-match already exists, skipping")
            return {"success": True, "message": "Non-match already exists"}

        # Add entries if they don't exist
        if not entry1_exists:
            scent_cross_brand_non_matches[scent_key].append(entry1_pair)
        if not entry2_exists:
            scent_cross_brand_non_matches[scent_key].append(entry2_pair)

        # Save atomically with sorting
        _atomic_write_yaml(
            scents_cross_brand_file, scent_cross_brand_non_matches, "scents_cross_brand"
        )

        logger.info("✅ Cross-brand scent non-match added and saved successfully")
        return {"success": True, "message": "Cross-brand scent non-match added successfully"}

    except Exception as e:
        logger.error(f"❌ Failed to add cross-brand scent non-match: {e}")
        raise
