#!/usr/bin/env python3
"""Override manager for extract phase field corrections."""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OverrideManager:
    """Manages loading and application of field overrides for extract phase."""

    # Valid field names that can be overridden
    VALID_FIELDS = {"razor", "blade", "brush", "soap"}

    def __init__(self, override_file_path: Path):
        """Initialize OverrideManager with path to override file.
        
        Args:
            override_file_path: Path to the YAML override file
        """
        self.override_file_path = override_file_path
        self.overrides: Dict[str, Dict[str, Dict[str, str]]] = {}

    def load_overrides(self) -> None:
        """Load overrides from YAML file with validation.
        
        Raises:
            ValueError: If override file has validation errors
            FileNotFoundError: If override file doesn't exist
            yaml.YAMLError: If YAML syntax is invalid
        """
        if not self.override_file_path.exists():
            # Override file is optional - pipeline continues normally
            logger.debug("Override file not found: %s", self.override_file_path)
            return

        try:
            with self.override_file_path.open("r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in override file: {e}")

        if content is None:
            # Empty file is valid
            logger.debug("Override file is empty: %s", self.override_file_path)
            return

        if not isinstance(content, dict):
            raise ValueError("Override file must contain a dictionary at root level")

        # Validate and load overrides
        duplicate_overrides = []
        for month, month_data in content.items():
            if not isinstance(month_data, dict):
                raise ValueError(f"Month '{month}' must contain a dictionary of comment overrides")

            month_overrides = {}
            for comment_id, field_data in month_data.items():
                if not isinstance(field_data, dict):
                    raise ValueError(
                        f"Comment '{comment_id}' in month '{month}' "
                        f"must contain field overrides"
                    )

                comment_overrides = {}
                for field, value in field_data.items():
                    # Validate field name
                    if field not in self.VALID_FIELDS:
                        raise ValueError(
                            f"Invalid field '{field}' in comment '{comment_id}' month '{month}'. "
                            f"Valid fields: {', '.join(sorted(self.VALID_FIELDS))}"
                        )

                    # Validate override value
                    if not isinstance(value, str):
                        raise ValueError(
                            f"Override value for field '{field}' in comment '{comment_id}' month '{month}' "
                            f"must be a string, got: {type(value).__name__}"
                        )
                    
                    if not value.strip():
                        raise ValueError(
                            f"Override value for field '{field}' in comment '{comment_id}' month '{month}' "
                            f"cannot be empty or whitespace-only"
                        )

                    # Check for reasonable length (prevent extremely long values)
                    if len(value.strip()) > 200:
                        raise ValueError(
                            f"Override value for field '{field}' in comment '{comment_id}' month '{month}' "
                            f"is too long ({len(value.strip())} characters). "
                            f"Maximum length: 200 characters"
                        )

                    # Check for duplicate overrides
                    override_key = f"{month}:{comment_id}:{field}"
                    if override_key in duplicate_overrides:
                        raise ValueError(
                            f"Duplicate override for field '{field}' in comment '{comment_id}' month '{month}'. "
                            f"Each comment+field combination can only have one override."
                        )
                    duplicate_overrides.append(override_key)

                    comment_overrides[field] = value.strip()

                if comment_overrides:
                    month_overrides[comment_id] = comment_overrides

            if month_overrides:
                self.overrides[month] = month_overrides

        logger.info("Loaded %d overrides from %s", len(duplicate_overrides), self.override_file_path)

    def get_override(self, month: str, comment_id: str, field: str) -> Optional[str]:
        """Get override value for specific field if it exists.
        
        Args:
            month: Month in YYYY-MM format
            comment_id: Reddit comment ID
            field: Field name to check for override
            
        Returns:
            Override value if exists, None otherwise
        """
        month_overrides = self.overrides.get(month, {})
        comment_overrides = month_overrides.get(comment_id, {})
        return comment_overrides.get(field)

    def validate_overrides(self, data: List[Dict[str, Any]]) -> None:
        """Validate that all override comment IDs exist in the data.
        
        Args:
            data: List of comment records to validate against
            
        Raises:
            ValueError: If any override references non-existent comment IDs
        """
        # Build set of existing comment IDs
        existing_ids = {record["id"] for record in data if "id" in record}
        
        # Check all override comment IDs exist
        missing_ids = []
        for month, month_overrides in self.overrides.items():
            for comment_id in month_overrides.keys():
                if comment_id not in existing_ids:
                    missing_ids.append(f"{month}:{comment_id}")

        if missing_ids:
            raise ValueError(
                f"Override file references non-existent comment IDs: {', '.join(missing_ids)}. "
                f"This usually means the override file is for a different dataset or the data has changed."
            )

    def apply_override(
        self, field_data: Optional[Dict[str, str]], override_value: str, field_exists: bool
    ) -> Dict[str, str]:
        """Apply override to field data, creating or modifying as needed.
        
        Args:
            field_data: Existing field data dict or None if field doesn't exist
            override_value: Value to use for override
            field_exists: Whether the field existed in original data
            
        Returns:
            Modified or created field data dict
        """
        if field_exists and field_data is not None:
            # Override existing field
            result = field_data.copy()
            result["normalized"] = override_value
            result["overridden"] = "Normalized"
            logger.debug("Applied override to existing field: %s -> %s", field_data.get("normalized"), override_value)
            return result
        else:
            # Create new field
            logger.debug("Created new field from override: %s", override_value)
            return {
                "original": override_value,
                "normalized": override_value,
                "overridden": "Original,Normalized",
            }

    def has_overrides(self) -> bool:
        """Check if any overrides are loaded.
        
        Returns:
            True if overrides exist, False otherwise
        """
        return bool(self.overrides)

    def get_override_summary(self) -> Dict[str, Any]:
        """Get summary statistics about loaded overrides.
        
        Returns:
            Dictionary with override statistics
        """
        total_overrides = 0
        month_counts = {}
        field_counts = {}
        
        for month, month_overrides in self.overrides.items():
            month_count = 0
            for comment_id, field_data in month_overrides.items():
                month_count += len(field_data)
                total_overrides += len(field_data)
                
                for field in field_data:
                    field_counts[field] = field_counts.get(field, 0) + 1
            
            month_counts[month] = month_count
        
        return {
            "total_overrides": total_overrides,
            "months_with_overrides": len(month_counts),
            "month_counts": month_counts,
            "field_counts": field_counts,
        }
