"""
Extract phase filtering module.

This module handles filtering of garbage entries during the extract phase
using regex patterns defined in data/extract_filters.yaml.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class ExtractFilter:
    """Filter for garbage entries during extraction."""

    def __init__(self, filter_path: Path = Path("data/extract_filters.yaml")):
        """
        Initialize the extract filter.

        Args:
            filter_path: Path to the filter configuration YAML file
        """
        self.filter_path = filter_path
        self.filters = self._load_filters()
        self.compiled_patterns = self._compile_patterns()

    def _load_filters(self) -> Dict:
        """Load filter configuration from YAML file."""
        try:
            if not self.filter_path.exists():
                logger.warning(f"Filter file not found: {self.filter_path}")
                return {
                    "razor": {"patterns": []},
                    "blade": {"patterns": []},
                    "brush": {"patterns": []},
                    "soap": {"patterns": []},
                    "global": [],
                }

            with open(self.filter_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {
                    "razor": {"patterns": []},
                    "blade": {"patterns": []},
                    "brush": {"patterns": []},
                    "soap": {"patterns": []},
                    "global": [],
                }
        except Exception as e:
            logger.error(f"Error loading filter file {self.filter_path}: {e}")
            return {
                "razor": {"patterns": []},
                "blade": {"patterns": []},
                "brush": {"patterns": []},
                "soap": {"patterns": []},
                "global": [],
            }

    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for efficient matching."""
        compiled = {"filters": {}, "global_filters": []}

        # Compile field-specific filters
        for field in ("razor", "blade", "brush", "soap"):
            compiled["filters"][field] = []
            field_config = self.filters.get(field, {})
            patterns = field_config.get("patterns", [])

            for pattern_str in patterns:
                try:
                    # Extract pattern from inline comment format: "pattern # comment"
                    if "#" in pattern_str:
                        pattern = pattern_str.split("#")[0].strip()
                        reason = pattern_str.split("#")[1].strip()
                    else:
                        pattern = pattern_str.strip()
                        reason = f"Matches pattern: {pattern}"

                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    compiled["filters"][field].append(
                        {"pattern": compiled_pattern, "reason": reason}
                    )
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{pattern_str}': {e}")

        # Compile global filters
        global_patterns = self.filters.get("global", [])
        for pattern_str in global_patterns:
            try:
                # Extract pattern from inline comment format: "pattern # comment"
                if "#" in pattern_str:
                    pattern = pattern_str.split("#")[0].strip()
                    reason = pattern_str.split("#")[1].strip()
                else:
                    pattern = pattern_str.strip()
                    reason = f"Global pattern: {pattern}"

                compiled_pattern = re.compile(pattern, re.IGNORECASE)
                compiled["global_filters"].append({"pattern": compiled_pattern, "reason": reason})
            except re.error as e:
                logger.error(f"Invalid global regex pattern '{pattern_str}': {e}")

        return compiled

    def should_skip_field(self, field: str, value: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a field value should be skipped based on filters.

        Args:
            field: Field name (razor, blade, brush, soap)
            value: Field value to check

        Returns:
            Tuple of (should_skip, reason) where reason is None if not skipped
        """
        # Check global filters first
        for filter_item in self.compiled_patterns["global_filters"]:
            if filter_item["pattern"].search(value):
                return True, filter_item["reason"]

        # Check field-specific filters
        field_filters = self.compiled_patterns["filters"].get(field, [])
        for filter_item in field_filters:
            if filter_item["pattern"].search(value):
                return True, filter_item["reason"]

        return False, None

    def filter_extracted_data(self, extracted_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter extracted data, separating valid entries from filtered ones.

        Args:
            extracted_data: List of extracted comment dictionaries

        Returns:
            Tuple of (valid_entries, filtered_entries)
        """
        valid_entries = []
        filtered_entries = []

        for entry in extracted_data:
            should_skip_entry = False
            skip_reasons = []

            # Check each extracted field
            for field in ("razor", "blade", "brush", "soap"):
                if field in entry:
                    should_skip, reason = self.should_skip_field(field, entry[field])
                    if should_skip:
                        should_skip_entry = True
                        skip_reasons.append(f"{field}: {reason}")

            if should_skip_entry:
                # Add filtering metadata to the entry
                entry["_filtered"] = True
                entry["_filter_reasons"] = skip_reasons
                filtered_entries.append(entry)
                logger.debug(f"Filtered entry: {skip_reasons}")
            else:
                valid_entries.append(entry)

        return valid_entries, filtered_entries


# Global filter instance for easy access
_filter_instance: Optional[ExtractFilter] = None


def get_filter() -> ExtractFilter:
    """Get the global filter instance, creating it if necessary."""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = ExtractFilter()
    return _filter_instance


def reset_filter() -> None:
    """Reset the global filter instance. Useful for testing."""
    global _filter_instance
    _filter_instance = None


def should_skip_field(field: str, value: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to check if a field should be skipped.

    Args:
        field: Field name (razor, blade, brush, soap)
        value: Field value to check

    Returns:
        Tuple of (should_skip, reason) where reason is None if not skipped
    """
    return get_filter().should_skip_field(field, value)


def filter_extracted_data(extracted_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Convenience function to filter extracted data.

    Args:
        extracted_data: List of extracted comment dictionaries

    Returns:
        Tuple of (valid_entries, filtered_entries)
    """
    return get_filter().filter_extracted_data(extracted_data)
