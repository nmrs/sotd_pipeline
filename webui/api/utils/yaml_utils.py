#!/usr/bin/env python3
"""YAML utilities for API operations."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load YAML file with error handling.

    Args:
        file_path: Path to the YAML file

    Returns:
        Loaded YAML data as dict, or None if loading fails

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            logger.info(f"Successfully loaded YAML file: {file_path}")
            return data
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {file_path}: {e}")
        raise
    except (OSError, IOError) as e:
        logger.error(f"File I/O error reading {file_path}: {e}")
        raise


def save_yaml_file(data: Dict[str, Any], file_path: Path) -> None:
    """Save data to YAML file with atomic write.

    Args:
        data: Data to save
        file_path: Path to save the YAML file

    Raises:
        yaml.YAMLError: If data cannot be serialized
        OSError: If file operations fail
    """
    # Create temporary file for atomic write
    temp_path = file_path.with_suffix(".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        # Atomic move
        temp_path.replace(file_path)
        logger.info(f"Successfully saved YAML file: {file_path}")
    except yaml.YAMLError as e:
        logger.error(f"YAML serialization error: {e}")
        raise
    except (OSError, IOError) as e:
        logger.error(f"File I/O error writing {file_path}: {e}")
        raise
    finally:
        # Clean up temp file if it still exists
        if temp_path.exists():
            temp_path.unlink()


def validate_yaml_structure(data: Any, expected_type: type = dict) -> bool:
    """Validate YAML data structure.

    Args:
        data: Data to validate
        expected_type: Expected type of the data

    Returns:
        True if data is valid, False otherwise
    """
    if not isinstance(data, expected_type):
        logger.error(f"Invalid data type: expected {expected_type}, got {type(data)}")
        return False

    if isinstance(expected_type, type) and expected_type is dict and not data:
        logger.warning("Empty dictionary provided")
        return False

    return True


def validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> bool:
    """Validate that required fields are present in data.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Returns:
        True if all required fields are present, False otherwise
    """
    if data is None:
        logger.error("Data is None, cannot validate required fields")
        return False

    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
        return False

    return True
