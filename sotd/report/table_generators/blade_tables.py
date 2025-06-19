#!/usr/bin/env python3
"""Table generators for blade-related data in the hardware report."""

from typing import Any

from .base import BaseTableGenerator


class BladesTableGenerator(BaseTableGenerator):
    """Table generator for individual blades in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blades data from aggregated data."""
        data = self.data.get("blades", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] blades data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] blades record {i} is not a dict")
                continue

            # Check for required fields - real data has 'name', 'shaves', 'unique_users'
            required_fields = ["name", "shaves"]
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                if self.debug:
                    print(f"[DEBUG] blades record {i} missing fields: {missing_fields}")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(f"[DEBUG] blades record {i} has invalid shaves: {record['shaves']}")
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blades"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the blades table."""
        return {
            "name": {"display_name": "Blade"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }


class BladeManufacturersTableGenerator(BaseTableGenerator):
    """Table generator for blade manufacturers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blade manufacturer data from aggregated data."""
        data = self.data.get("blade_manufacturers", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] blade_manufacturers data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] blade_manufacturers record {i} is not a dict")
                continue

            # Check for required fields
            if "brand" not in record or "shaves" not in record:
                if self.debug:
                    print(f"[DEBUG] blade_manufacturers record {i} missing required fields")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(
                        f"[DEBUG] blade_manufacturers record {i} has invalid shaves: "
                        f"{record['shaves']}"
                    )
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blade Manufacturers"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the blade manufacturers table."""
        return {
            "brand": {"display_name": "Brand"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }
