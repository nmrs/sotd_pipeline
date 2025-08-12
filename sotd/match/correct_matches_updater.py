"""Correct matches updater for managing correct_matches.yaml file operations."""

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class CorrectMatchesUpdater:
    """Handle YAML file operations for correct_matches.yaml."""

    def __init__(self, correct_matches_path: Optional[Path] = None):
        """Initialize updater with path to correct_matches.yaml."""
        self.correct_matches_path = correct_matches_path or Path("data/correct_matches.yaml")
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensure the directory for correct_matches.yaml exists."""
        self.correct_matches_path.parent.mkdir(parents=True, exist_ok=True)

    def load_correct_matches(self) -> Dict[str, Any]:
        """Load existing correct_matches.yaml file."""
        if not self.correct_matches_path.exists():
            return {}

        try:
            with open(self.correct_matches_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except (yaml.YAMLError, FileNotFoundError):
            # If file is corrupted or can't be loaded, return empty dict
            # This allows the system to continue and recreate the file
            return {}

    def add_or_update_entry(
        self,
        input_text: str,
        result_data: Dict[str, Any],
        action_type: str,
        field_type: str = "brush",
    ) -> None:
        """
        Add new entry or update existing one in correct_matches.yaml.

        Args:
            input_text: The input text to match (normalized)
            result_data: The result data to store
            action_type: Type of action ("validated" or "overridden")
            field_type: Field type ("brush", "handle", "knot", etc.)
        """
        # Load existing data
        data = self.load_correct_matches()

        # Normalize input text for case-insensitive lookup
        normalized_text = input_text.lower().strip()

        # For brush field, use the hierarchical structure
        if field_type == "brush":
            # Ensure field section exists
            if field_type not in data:
                data[field_type] = {}

            # Extract brand and model from result data
            brand = result_data.get("brand")
            model = result_data.get("model")

            if brand:
                # Ensure brand section exists
                if brand not in data[field_type]:
                    data[field_type][brand] = {}

                # Handle dual-component brushes where model is null
                if model is None:
                    # For dual-component brushes, use a special model identifier
                    # This allows them to be stored in correct_matches.yaml
                    model_key = "dual_component"
                else:
                    model_key = model

                # Ensure model section exists
                if model_key not in data[field_type][brand]:
                    data[field_type][brand][model_key] = []

                # Add the normalized text as a pattern if not already present
                if normalized_text not in data[field_type][brand][model_key]:
                    data[field_type][brand][model_key].append(normalized_text)

        # For handle and knot fields, use flat structure
        elif field_type in ["handle", "knot"]:
            # Ensure field section exists
            if field_type not in data:
                data[field_type] = {}

            # Add entry with normalized text as key
            data[field_type][normalized_text] = result_data

        # For split_brush field, store handle/knot mapping
        elif field_type == "split_brush":
            # Extract handle and knot components from the dual-component brush
            handle_data = result_data.get("handle", {})
            knot_data = result_data.get("knot", {})

            if handle_data and knot_data:
                # Store handle component in handle section
                handle_brand = handle_data.get("brand")
                handle_model = handle_data.get("model")

                if handle_brand and handle_model:
                    # Ensure handle section exists
                    if "handle" not in data:
                        data["handle"] = {}
                    if handle_brand not in data["handle"]:
                        data["handle"][handle_brand] = {}
                    if handle_model not in data["handle"][handle_brand]:
                        data["handle"][handle_brand][handle_model] = []

                    # Add the normalized text to handle section if not already present
                    if normalized_text not in data["handle"][handle_brand][handle_model]:
                        data["handle"][handle_brand][handle_model].append(normalized_text)

                # Store knot component in knot section
                knot_brand = knot_data.get("brand")
                knot_model = knot_data.get("model")

                if knot_brand and knot_model:
                    # Ensure knot section exists
                    if "knot" not in data:
                        data["knot"] = {}
                    if knot_brand not in data["knot"]:
                        data["knot"][knot_brand] = {}
                    if knot_model not in data["knot"][knot_brand]:
                        data["knot"][knot_brand][knot_model] = []

                    # Add the normalized text to knot section if not already present
                    if normalized_text not in data["knot"][knot_brand][knot_model]:
                        data["knot"][knot_brand][knot_model].append(normalized_text)
            else:
                # Fallback: if we can't extract components, store as regular brush
                # This shouldn't happen with proper dual-component data
                if "brush" not in data:
                    data["brush"] = {}
                if "dual_component" not in data["brush"]:
                    data["brush"]["dual_component"] = []
                if normalized_text not in data["brush"]["dual_component"]:
                    data["brush"]["dual_component"].append(normalized_text)

        # Save the updated data
        self.save_correct_matches(data)

    def save_correct_matches(self, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Save data to correct_matches.yaml using atomic write operations.

        Args:
            data: Data to save, or None to use current data
        """
        if data is None:
            data = self.load_correct_matches()

        # Create temporary file for atomic write
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )

        try:
            # Write to temporary file
            yaml.dump(
                data,
                temp_file,
                default_flow_style=False,
                sort_keys=True,
                allow_unicode=True,
                indent=2,
            )
            temp_file.close()

            # Atomic move to final location
            shutil.move(temp_file.name, self.correct_matches_path)

        except Exception as e:
            # Clean up temporary file on error
            if temp_file.name:
                try:
                    Path(temp_file.name).unlink(missing_ok=True)
                except Exception:
                    pass
            raise e

    def remove_entry(self, input_text: str, field_type: str = "brush") -> bool:
        """
        Remove an entry from correct_matches.yaml.

        Args:
            input_text: The input text to remove
            field_type: Field type to remove from

        Returns:
            True if entry was removed, False if not found
        """
        data = self.load_correct_matches()
        normalized_text = input_text.lower().strip()

        if field_type not in data:
            return False

        if field_type == "brush":
            # Search through brand/model hierarchy
            for brand in data[field_type]:
                for model in data[field_type][brand]:
                    if normalized_text in data[field_type][brand][model]:
                        data[field_type][brand][model].remove(normalized_text)
                        # Remove empty model sections
                        if not data[field_type][brand][model]:
                            del data[field_type][brand][model]
                        # Remove empty brand sections
                        if not data[field_type][brand]:
                            del data[field_type][brand]
                        self.save_correct_matches(data)
                        return True
        else:
            # For flat structures like handle, knot, split_brush
            if normalized_text in data[field_type]:
                del data[field_type][normalized_text]
                self.save_correct_matches(data)
                return True

        return False

    def get_entry(self, input_text: str, field_type: str = "brush") -> Optional[Dict[str, Any]]:
        """
        Get an entry from correct_matches.yaml.

        Args:
            input_text: The input text to look up
            field_type: Field type to search in

        Returns:
            Entry data if found, None otherwise
        """
        data = self.load_correct_matches()
        normalized_text = input_text.lower().strip()

        if field_type not in data:
            return None

        if field_type == "brush":
            # Search through brand/model hierarchy
            for brand in data[field_type]:
                for model in data[field_type][brand]:
                    if normalized_text in data[field_type][brand][model]:
                        return {"brand": brand, "model": model, "pattern": normalized_text}
        else:
            # For flat structures like handle, knot, split_brush
            if normalized_text in data[field_type]:
                return data[field_type][normalized_text]

        return None

    def has_entry(self, input_text: str, field_type: str = "brush") -> bool:
        """
        Check if an entry exists in correct_matches.yaml.

        Args:
            input_text: The input text to check
            field_type: Field type to search in

        Returns:
            True if entry exists, False otherwise
        """
        return self.get_entry(input_text, field_type) is not None
