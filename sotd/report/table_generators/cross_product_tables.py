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


class RazorBladeCombinationsTableGenerator(DataTransformingTableGenerator, NoDeltaMixin):
    """Table generator for razor-blade combinations in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor-blade combinations data from aggregated data."""
        data = self.data.get("razor_blade_combinations", [])
        # No filtering - show all combinations as template doesn't specify limits
        valid_data = self._validate_data_records(
            data, "razor_blade_combinations", ["name", "shaves", "rank"]
        )

        # Map name field directly (already contains "Razor + Blade" format)
        result = []
        for record in valid_data:
            name = record.get("name")
            if name:
                result.append(
                    {
                        "rank": record.get("rank", 0),
                        "name": name,
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

    def _get_category_name(self) -> str:
        """Get the category name for this table generator."""
        return "razor_blade_combinations"

    def _get_source_field(self) -> str:
        """Get the source field name in historical data."""
        return "name"

    def _get_target_field(self) -> str:
        """Get the target field name in current data."""
        return "name"


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

    def _format_existing_ranks_with_proper_ties(
        self, data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format existing ranks with proper tie detection for use count tables.

        This method overrides the base class method to handle the 'uses' field
        instead of 'shaves' and 'unique_users' fields.
        """
        if not data:
            return data

        # Sort data by uses (desc) for consistent tie detection
        sorted_data = sorted(data, key=lambda x: x.get("uses", 0), reverse=True)

        # Detect ties based on actual uses values, not just rank numbers
        numeric_ranks = []
        current_rank = 1

        for i, item in enumerate(sorted_data):
            if i > 0:
                prev_item = sorted_data[i - 1]
                # Check if this item is tied with the previous one based on uses
                if item.get("uses", 0) == prev_item.get("uses", 0):
                    # Tied with previous - use same rank
                    numeric_ranks.append(numeric_ranks[-1])
                else:
                    # New rank - account for ties by using position + 1
                    current_rank = i + 1
                    numeric_ranks.append(current_rank)
            else:
                # First item gets rank 1
                numeric_ranks.append(1)

        # Use the rank formatter to get formatted ranks with tie indicators
        formatted_ranks = self._format_ranks_with_ties(numeric_ranks)

        # Update rank data in each item, preserving the original order
        for i, item in enumerate(sorted_data):
            item["rank"] = formatted_ranks[i]

        # Return data in original order (not sorted order)
        return data

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
