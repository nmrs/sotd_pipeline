#!/usr/bin/env python3
"""Table generators for blade-related data in the hardware report."""

from typing import Any

from .base import ManufacturerTableGenerator, StandardProductTableGenerator


class BladesTableGenerator(StandardProductTableGenerator):
    """Table generator for individual blades in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blades data from aggregated data."""
        data = self.data.get("blades", [])
        return self._validate_data_records(data, "blades", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blades"


class BladeManufacturersTableGenerator(ManufacturerTableGenerator):
    """Table generator for blade manufacturers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blade manufacturer data from aggregated data."""
        data = self.data.get("blade_manufacturers", [])
        return self._validate_data_records(data, "blade_manufacturers", ["brand", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blade Manufacturers"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "brand"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the blade manufacturers table."""
        return {
            "brand": {"display_name": "name"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }
