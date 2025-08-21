#!/usr/bin/env python3
"""Cross-product table generators for the report phase."""

from typing import Any

from .base import (
    STANDARD_USE_COUNT_COLUMNS,
    BaseTableGenerator,
    NoDeltaMixin,
    UseCountTableFactory,
)
from .specialized_tables import DataTransformingTableGenerator


class RazorBladeCombinationsTableGenerator(DataTransformingTableGenerator):
    """Table generator for razor-blade combinations in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor-blade combinations data from aggregated data."""
        data = self.data.get("razor_blade_combinations", [])
        # No filtering - show all combinations as template doesn't specify limits
        valid_data = self._validate_data_records(
            data, "razor_blade_combinations", ["razor", "blade", "shaves"]
        )

        # Map razor and blade to plate field
        result = []
        for record in valid_data:
            razor = record.get("razor")
            blade = record.get("blade")
            if razor and blade:
                result.append(
                    {
                        "plate": f"{razor} + {blade}",
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        if self.debug:
            print(f"[DEBUG] Found {len(result)} valid razor-blade combination records")

        return result

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


class HighestUseCountPerBladeTableGenerator(UseCountTableFactory, NoDeltaMixin):
    """Table generator for highest use count per blade in the hardware report."""

    def __init__(self, data: dict[str, Any], debug: bool = False):
        """Initialize the table generator."""
        super().__init__(data, "highest_use_count_per_blade", "Highest Use Count per Blade", debug)

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get highest use count per blade data from aggregated data."""
        # Handle both full structure and extracted data section
        # Full structure: data['data']['highest_use_count_per_blade']
        # Extracted data: data['highest_use_count_per_blade']
        if "data" in self.data and "highest_use_count_per_blade" in self.data["data"]:
            # Full structure (when called directly)
            data = self.data["data"]["highest_use_count_per_blade"]
        else:
            # Extracted data section (when called via TableGenerator)
            data = self.data.get("highest_use_count_per_blade", [])

        # Trace ranks at input
        if self.debug:
            from ..utils.rank_tracer import trace_ranks

            trace_ranks("HighestUseCountPerBladeTableGenerator.input", data)

        # No filtering - show all entries as template doesn't specify limits
        valid_data = self._validate_data_records(
            data, "highest_use_count_per_blade", ["rank", "user", "blade", "uses"]
        )

        # Trace ranks after validation
        if self.debug:
            from ..utils.rank_tracer import trace_ranks

            trace_ranks("HighestUseCountPerBladeTableGenerator.after_validation", valid_data)

        # Transform data for table display
        for record in valid_data:
            # Add u/ prefix to username for Reddit formatting (only if not already present)
            if not record["user"].startswith("u/"):
                record["user"] = f"u/{record['user']}"
            # Ensure rank is preserved from aggregator data
            if "rank" not in record:
                record["rank"] = 0  # Fallback if rank is missing

        # Trace ranks at output
        if self.debug:
            from ..utils.rank_tracer import trace_ranks

            trace_ranks("HighestUseCountPerBladeTableGenerator.output", valid_data)

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
