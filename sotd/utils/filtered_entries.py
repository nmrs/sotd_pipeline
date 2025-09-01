"""Utilities for managing intentionally unmatched entries."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class FilteredEntriesManager:
    """Manages intentionally unmatched entries stored in YAML format."""

    def __init__(self, file_path: Path):
        """Initialize with the path to the YAML file."""
        self.file_path = file_path
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def load(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Load filtered entries from YAML file."""
        if not self.file_path.exists():
            # Create empty structure if file doesn't exist
            self._data = {
                "razor": {},
                "brush": {},
                "blade": {},
                "soap": {},
            }
            self.save()
            return self._data

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}

            # Ensure all categories exist
            for category in ["razor", "brush", "blade", "soap"]:
                if category not in self._data:
                    self._data[category] = {}

            return self._data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {self.file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading filtered entries from {self.file_path}: {e}")

    def save(self) -> None:
        """Save filtered entries to YAML file."""
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._data, f, default_flow_style=False, sort_keys=True, allow_unicode=True
                )
        except Exception as e:
            raise ValueError(f"Error saving filtered entries to {self.file_path}: {e}")

    def add_entry(
        self,
        category: str,
        entry_name: str,
        comment_id: str,
        file_path: str,
        source: str = "user",
        reason: Optional[str] = None,
    ) -> None:
        """Add an entry to the filtered list (case-insensitive)."""
        if category not in self._data:
            self._data[category] = {}

        # Normalize key to lowercase for consistency
        key_name = entry_name.lower()

        if key_name not in self._data[category]:
            self._data[category][key_name] = {
                "added_date": datetime.now().strftime("%Y-%m-%d"),
                "comment_ids": [],
            }

            # Add reason field if provided
            if reason:
                self._data[category][key_name]["reason"] = reason

        # Check if comment_id already exists
        comment_ids = self._data[category][key_name]["comment_ids"]
        for existing in comment_ids:
            if existing["id"] == comment_id and existing["file"] == file_path:
                return  # Already exists, no need to add

        # Add new comment_id
        comment_ids.append({"file": file_path, "id": comment_id, "source": source})

    def remove_entry(self, category: str, entry_name: str, comment_id: str, file_path: str) -> bool:
        """Remove a specific comment_id from an entry (case-insensitive)."""
        if category not in self._data:
            return False

        # Case-insensitive lookup
        entry_name_lower = entry_name.lower()
        for key in self._data[category].keys():
            if key.lower() == entry_name_lower:
                comment_ids = self._data[category][key]["comment_ids"]
                for i, existing in enumerate(comment_ids):
                    if existing["id"] == comment_id and existing["file"] == file_path:
                        comment_ids.pop(i)

                        # Remove entry entirely if no more comment_ids
                        if not comment_ids:
                            del self._data[category][key]

                        return True
                break

        return False

    def is_filtered(self, category: str, entry_name: str) -> bool:
        """Check if an entry is in the filtered list (case-insensitive)."""
        if category not in self._data:
            return False

        # Case-insensitive lookup
        entry_name_lower = entry_name.lower()
        for key in self._data[category].keys():
            if key.lower() == entry_name_lower:
                return len(self._data[category][key]["comment_ids"]) > 0

        return False

    def get_filtered_entries(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get all filtered entries, optionally filtered by category."""
        if category:
            return {category: self._data.get(category, {})}
        return self._data

    def get_entry_comment_ids(self, category: str, entry_name: str) -> List[Dict[str, str]]:
        """Get all comment_ids for a specific entry (case-insensitive)."""
        if category not in self._data:
            return []

        # Case-insensitive lookup
        entry_name_lower = entry_name.lower()
        for key in self._data[category].keys():
            if key.lower() == entry_name_lower:
                return self._data[category][key].get("comment_ids", [])

        return []

    def validate_data(self) -> Tuple[bool, List[str]]:
        """Validate the data structure and return (is_valid, error_messages)."""
        errors = []

        if not isinstance(self._data, dict):
            errors.append("Root data must be a dictionary")
            return False, errors

        valid_categories = {"razor", "brush", "blade", "soap"}

        for category, entries in self._data.items():
            if category not in valid_categories:
                errors.append(f"Invalid category: {category}")
                continue

            if not isinstance(entries, dict):
                errors.append(f"Category {category} must be a dictionary")
                continue

            for entry_name, metadata in entries.items():
                if not isinstance(metadata, dict):
                    errors.append(f"Metadata for {category}/{entry_name} must be a dictionary")
                    continue

                if "added_date" not in metadata:
                    errors.append(f"Missing added_date for {category}/{entry_name}")

                if "comment_ids" not in metadata:
                    errors.append(f"Missing comment_ids for {category}/{entry_name}")
                    continue

                if not isinstance(metadata["comment_ids"], list):
                    errors.append(f"comment_ids for {category}/{entry_name} must be a list")
                    continue

                for i, comment_id in enumerate(metadata["comment_ids"]):
                    if not isinstance(comment_id, dict):
                        errors.append(
                            f"Comment ID {i} for {category}/{entry_name} must be a dictionary"
                        )
                        continue

                    required_fields = {"file", "id", "source"}
                    missing_fields = required_fields - set(comment_id.keys())
                    if missing_fields:
                        errors.append(
                            f"Missing fields {missing_fields} in comment_id {i} "
                            f"for {category}/{entry_name}"
                        )

        return len(errors) == 0, errors


def load_filtered_entries(file_path: Path) -> FilteredEntriesManager:
    """Load filtered entries from the specified file."""
    manager = FilteredEntriesManager(file_path)
    manager.load()
    return manager


def save_filtered_entries(manager: FilteredEntriesManager) -> None:
    """Save filtered entries using the manager."""
    manager.save()
