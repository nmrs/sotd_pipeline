"""Base validator class for product-type validation logic."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    validation_errors: Optional[List[str]] = None


class BaseValidator:
    """Base class for product-type validators."""

    def __init__(self, yaml_path: Path):
        """Initialize the validator with a YAML file path."""
        self.yaml_path = yaml_path
        self.data: Dict[str, Any] = {}
        self.is_loaded: bool = False

    def load_data(self) -> ValidationResult:
        """Load data from the YAML file."""
        try:
            if not self.yaml_path.exists():
                return ValidationResult(success=False, error_message="File not found")

            with open(self.yaml_path, "r") as f:
                self.data = yaml.safe_load(f) or {}

            self.is_loaded = True
            return ValidationResult(success=True, data=self.data)

        except yaml.YAMLError:
            return ValidationResult(success=False, error_message="Invalid YAML")
        except Exception as e:
            return ValidationResult(success=False, error_message=str(e))

    def save_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Save data to the YAML file."""
        try:
            # Ensure directory exists
            self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.yaml_path, "w") as f:
                yaml.dump(data, f, allow_unicode=True)

            self.data = data
            return ValidationResult(success=True)

        except FileNotFoundError:
            return ValidationResult(success=False, error_message="Directory not found")
        except Exception as e:
            return ValidationResult(success=False, error_message=str(e))

    def validate_required_fields(self, required_fields: List[str]) -> ValidationResult:
        """Validate that required fields are present in all items."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        errors = []
        items = self.data.get("items", {})

        for item_name, item_data in items.items():
            for field in required_fields:
                if field not in item_data:
                    errors.append(f"Item '{item_name}' missing required field '{field}'")

        return ValidationResult(success=len(errors) == 0, validation_errors=errors)

    def validate_data_structure(self, expected_structure: Dict[str, type]) -> ValidationResult:
        """Validate the overall data structure."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        errors = []

        for key, expected_type in expected_structure.items():
            if key not in self.data:
                errors.append(f"Missing required key '{key}' in data structure")
            elif not isinstance(self.data[key], expected_type):
                errors.append(f"Key '{key}' has wrong type, expected {expected_type.__name__}")

        return ValidationResult(success=len(errors) == 0, validation_errors=errors)

    def get_item_by_name(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Get an item by name."""
        if not self.is_loaded:
            return None

        items = self.data.get("items", {})
        return items.get(item_name)

    def get_all_items(self) -> Dict[str, Dict[str, Any]]:
        """Get all items."""
        if not self.is_loaded:
            return {}

        return self.data.get("items", {})

    def add_item(self, item_name: str, item_data: Dict[str, Any]) -> ValidationResult:
        """Add a new item."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        items = self.data.get("items", {})
        if item_name in items:
            return ValidationResult(
                success=False, error_message=f"Item '{item_name}' already exists"
            )

        items[item_name] = item_data
        self.data["items"] = items

        return ValidationResult(success=True)

    def update_item(self, item_name: str, item_data: Dict[str, Any]) -> ValidationResult:
        """Update an existing item."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        items = self.data.get("items", {})
        if item_name not in items:
            return ValidationResult(success=False, error_message=f"Item '{item_name}' not found")

        items[item_name] = item_data
        self.data["items"] = items

        return ValidationResult(success=True)

    def delete_item(self, item_name: str) -> ValidationResult:
        """Delete an item."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        items = self.data.get("items", {})
        if item_name not in items:
            return ValidationResult(success=False, error_message=f"Item '{item_name}' not found")

        del items[item_name]
        self.data["items"] = items

        return ValidationResult(success=True)

    def validate_item_data(
        self, item_data: Dict[str, Any], required_fields: List[str]
    ) -> ValidationResult:
        """Validate individual item data."""
        errors = []

        for field in required_fields:
            if field not in item_data:
                errors.append(f"Missing required field '{field}'")

        return ValidationResult(success=len(errors) == 0, validation_errors=errors)

    def backup_data(self, backup_path: Path) -> ValidationResult:
        """Backup current data to a file."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        try:
            with open(backup_path, "w") as f:
                yaml.dump(self.data, f, allow_unicode=True)

            return ValidationResult(success=True)

        except Exception as e:
            return ValidationResult(success=False, error_message=str(e))

    def restore_data(self, backup_path: Path) -> ValidationResult:
        """Restore data from a backup file."""
        try:
            if not backup_path.exists():
                return ValidationResult(success=False, error_message="Backup file not found")

            with open(backup_path, "r") as f:
                self.data = yaml.safe_load(f) or {}

            self.is_loaded = True
            return ValidationResult(success=True, data=self.data)

        except yaml.YAMLError:
            return ValidationResult(success=False, error_message="Invalid YAML in backup file")
        except Exception as e:
            return ValidationResult(success=False, error_message=str(e))
