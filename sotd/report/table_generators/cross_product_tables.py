#!/usr/bin/env python3
"""Cross-product table generators for the report phase."""

from typing import Any

from .base import (
    STANDARD_USE_COUNT_COLUMNS,
    BaseTableGenerator,
    NoDeltaMixin,
    StandardProductTableGenerator,
)


class RazorBladeCombinationsTableGenerator(StandardProductTableGenerator, NoDeltaMixin):
    """Table generator for razor-blade combinations in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor-blade combination data from aggregated data."""
        data = self.data.get("razor_blade_combinations", [])
        # Filter for combinations with 5+ shaves (as requested by user)
        filtered_data = [item for item in data if item.get("shaves", 0) >= 5]
        return self._validate_data_records(
            filtered_data, "razor_blade_combinations", ["name", "shaves"]
        )

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Most Used Blades in Most Used Razors"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the razor-blade combinations table."""
        from .base import STANDARD_PRODUCT_COLUMNS

        # Override the name column to show "Razor + Blade"
        config = STANDARD_PRODUCT_COLUMNS.copy()
        config["name"]["display_name"] = "Razor + Blade"
        return config

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all combinations with 5+ shaves."""
        return False


class HighestUseCountPerBladeTableGenerator(StandardProductTableGenerator, NoDeltaMixin):
    """Table generator for highest use count per blade in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get highest use count per blade data from aggregated data."""
        data = self.data.get("highest_use_count_per_blade", [])
        # Filter for entries with 5+ uses (as requested by user)
        filtered_data = [item for item in data if item.get("uses", 0) >= 5]
        valid_data = self._validate_data_records(
            filtered_data, "highest_use_count_per_blade", ["user", "blade", "uses"]
        )

        # Add a name field for delta calculations (combine user and blade)
        for record in valid_data:
            record["name"] = f"{record['user']} - {record['blade']}"
            # Add u/ prefix to username for Reddit formatting
            record["user"] = f"u/{record['user']}"

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Highest Use Count per Blade"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the highest use count per blade table."""
        return STANDARD_USE_COUNT_COLUMNS

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all entries with 5+ uses."""
        return False


# Factory method alternatives for simplified table creation
def create_razor_blade_combinations_table(
    data: dict[str, Any], debug: bool = False
) -> BaseTableGenerator:
    """Create a razor-blade combinations table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data,
        category="razor_blade_combinations",
        title="Most Used Blades in Most Used Razors",
        name_key="name",
        debug=debug,
    )


def create_highest_use_count_per_blade_table(
    data: dict[str, Any], debug: bool = False
) -> BaseTableGenerator:
    """Create a highest use count per blade table using factory method."""
    return BaseTableGenerator.create_use_count_table(
        data=data,
        category="highest_use_count_per_blade",
        title="Highest Use Count per Blade",
        debug=debug,
    )
