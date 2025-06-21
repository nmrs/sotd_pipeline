#!/usr/bin/env python3
"""Table generators for blade-related data in the hardware report."""

from typing import Any

from .base import BaseTableGenerator, StandardProductTableGenerator


class BladesTableGenerator(StandardProductTableGenerator):
    """Table generator for individual blades in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blades data from aggregated data."""
        data = self.data.get("blades", [])
        return self._validate_data_records(data, "blades", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blades"


class BladeManufacturersTableGenerator(StandardProductTableGenerator):
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


# Factory method alternatives for simplified table creation
def create_blades_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a blades table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data, category="blades", title="Blades", name_key="name", debug=debug
    )


def create_blade_manufacturers_table(
    data: dict[str, Any], debug: bool = False
) -> BaseTableGenerator:
    """Create a blade manufacturers table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data,
        category="blade_manufacturers",
        title="Blade Manufacturers",
        name_key="brand",
        debug=debug,
    )
