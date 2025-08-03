"""
Extract phase filtering module.

Filters extracted data based on patterns defined in YAML configuration.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from sotd.match.utils.regex_error_utils import compile_regex_with_context

logger = logging.getLogger(__name__)


class ExtractFilter:
    """
    Filter extracted data based on patterns defined in YAML configuration.

    Supports field-specific filters and global filters that apply to all fields.
    """

    def __init__(self, filter_path: Path = Path("data/extract_filters.yaml")):
        """
        Initialize filter with configuration from YAML file.

        Args:
            filter_path: Path to filter configuration file
        """
        self.filter_path = filter_path
        self.filters = self._load_filters()
        self.compiled_patterns = self._compile_patterns()

    def _load_filters(self) -> Dict:
        """
        Load filter configuration from YAML file.

        Returns:
            Dictionary containing filter configuration
        """
        default_filters = {
            "razor": {"patterns": []},
            "blade": {"patterns": []},
            "brush": {"patterns": []},
            "soap": {"patterns": []},
            "global": [],
        }

        if not self.filter_path.exists():
            logger.warning(f"Filter file not found: {self.filter_path}")
            return default_filters

        try:
            with open(self.filter_path, "r", encoding="utf-8") as f:
                filters = yaml.safe_load(f)
                if not filters:
                    return default_filters
                return filters
        except yaml.YAMLError as e:
            logger.error(f"Error loading filter file {self.filter_path}: {e}")
            return default_filters

    def _compile_patterns(self) -> Dict:
        """
        Compile regex patterns for efficient matching with enhanced error reporting.

        Returns:
            Dictionary containing compiled patterns
        """
        compiled = {
            "filters": {
                "razor": [],
                "blade": [],
                "brush": [],
                "soap": [],
            },
            "global_filters": [],
        }

        # Compile field-specific filters
        for field in ("razor", "blade", "brush", "soap"):
            field_patterns = self.filters.get(field, {}).get("patterns", [])
            for pattern_str in field_patterns:
                # Extract pattern from inline comment format: "pattern # comment"
                if "#" in pattern_str:
                    pattern = pattern_str.split("#")[0].strip()
                    reason = pattern_str.split("#")[1].strip()
                else:
                    pattern = pattern_str.strip()
                    reason = f"Matches pattern: {pattern}"

                # Create context for enhanced error reporting
                context = {"file": str(self.filter_path), "field": field}
                compiled_pattern = compile_regex_with_context(pattern, context)
                compiled["filters"][field].append({"pattern": compiled_pattern, "reason": reason})

        # Compile global filters
        global_patterns = self.filters.get("global", [])
        for pattern_str in global_patterns:
            # Extract pattern from inline comment format: "pattern # comment"
            if "#" in pattern_str:
                pattern = pattern_str.split("#")[0].strip()
                reason = pattern_str.split("#")[1].strip()
            else:
                pattern = pattern_str.strip()
                reason = f"Global pattern: {pattern}"

            # Create context for enhanced error reporting
            context = {"file": str(self.filter_path), "field": "global"}
            compiled_pattern = compile_regex_with_context(pattern, context)
            compiled["global_filters"].append({"pattern": compiled_pattern, "reason": reason})

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
