#!/usr/bin/env python3
"""Table generators for blade-related data in the hardware report."""

from typing import Any

from .base import (
    BaseTableGenerator,
    DataValidationMixin,
    ManufacturerTableGenerator,
    StandardProductTableGenerator,
)


class BladesTableGenerator(StandardProductTableGenerator):
    """Table generator for individual blades in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blades data from aggregated data."""
        data = self.data.get("blades", [])
        # No filtering - show all blades as template doesn't specify limits
        return self._validate_data_records(data, "blades", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blades"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration with blade-specific display names."""
        import copy

        config = copy.deepcopy(super().get_column_config())
        config["name"]["display_name"] = "Blade"
        return config

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all blades."""
        return False


class BladeManufacturersTableGenerator(ManufacturerTableGenerator):
    """Table generator for blade manufacturers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blade manufacturer data from aggregated data."""
        data = self.data.get("blade_manufacturers", [])
        # No filtering - show all manufacturers as template doesn't specify limits
        return self._validate_data_records(data, "blade_manufacturers", ["brand", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blade Manufacturers"

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all manufacturers."""
        return False


class BladeUsageDistributionTableGenerator(BaseTableGenerator, DataValidationMixin):
    """Generates a table of blade usage distribution statistics."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get blade usage distribution data from aggregated data."""
        data = self.data.get("blade_usage_distribution", [])
        return self._validate_data_records(
            data, "blade_usage_distribution", ["use_count", "shaves"]
        )

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Blade Usage Distribution"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for blade usage distribution table."""
        return {
            "rank": {"display_name": "Rank"},
            "use_count": {
                "display_name": "Uses per Blade",
                "format": "number",
                "sort_order": "asc",
            },
            "shaves": {
                "display_name": "Total Shaves",
                "format": "number",
                "sort_order": "desc",
            },
            "unique_users": {
                "display_name": "Unique Users",
                "format": "number",
                "sort_order": "desc",
            },
        }

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all usage levels."""
        return False


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
