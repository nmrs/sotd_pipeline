#!/usr/bin/env python3
"""Override manager for extract phase field corrections."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


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
            return

        try:
            with self.override_file_path.open("r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in override file: {e}")

        if content is None:
            # Empty file is valid
            return

        if not isinstance(content, dict):
            raise ValueError("Override file must contain a dictionary at root level")

        # Validate and load overrides
        for month, month_data in content.items():
            if not isinstance(month_data, dict):
                raise ValueError(
                    f"Month '{month}' must contain a dictionary of comment overrides"
                )

            month_overrides = {}
            for comment_id, field_data in month_data.items():
                if not isinstance(field_data, dict):
                    raise ValueError(
                        f"Comment '{comment_id}' in month '{month}' "
                        f"must contain field overrides"
                    )

                comment_overrides = {}
                for field, value in field_data.items():
                    if field not in self.VALID_FIELDS:
                        raise ValueError(
                            f"Invalid field '{field}' in comment '{comment_id}' month '{month}'. "
                            f"Valid fields: {', '.join(sorted(self.VALID_FIELDS))}"
                        )

                    if not isinstance(value, str) or not value.strip():
                        raise ValueError(
                            f"Override value for field '{field}' in comment '{comment_id}' month '{month}' "
                            f"must be a non-empty string, got: {repr(value)}"
                        )

                    comment_overrides[field] = value.strip()

                if comment_overrides:
                    month_overrides[comment_id] = comment_overrides

            if month_overrides:
                self.overrides[month] = month_overrides

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
                f"Override file references non-existent comment IDs: {', '.join(missing_ids)}"
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
            return result
        else:
            # Create new field
            return {
                "original": override_value,
                "normalized": override_value,
                "overridden": "Original,Normalized"
            }

    def has_overrides(self) -> bool:
        """Check if any overrides are loaded.
        
        Returns:
            True if overrides exist, False otherwise
        """
        return bool(self.overrides)
