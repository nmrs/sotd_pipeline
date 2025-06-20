#!/usr/bin/env python3
"""Cross-product table generators for the report phase."""

from typing import Any, Dict, Optional

from .base import BaseTableGenerator


class RazorBladeCombinationsTableGenerator(BaseTableGenerator):
    """Table generator for razor-blade combinations in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor-blade combination data from aggregated data."""
        data = self.data.get("razor_blade_combinations", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] razor_blade_combinations data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] razor_blade_combinations record {i} is not a dict")
                continue

            # Check for required fields - real data has 'name', 'shaves', 'unique_users'
            required_fields = ["name", "shaves"]
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                if self.debug:
                    print(
                        f"[DEBUG] razor_blade_combinations record {i} missing fields: "
                        f"{missing_fields}"
                    )
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(
                        f"[DEBUG] razor_blade_combinations record {i} has invalid shaves: "
                        f"{record['shaves']}"
                    )
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Most Used Blades in Most Used Razors"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the razor-blade combinations table."""
        return {
            "name": {"display_name": "Razor + Blade"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def generate_table(
        self,
        max_rows: int = 20,
        include_delta: bool = False,
        comparison_data: Optional[Dict[str, Any]] = None,
        comparison_period: str = "previous month",
    ) -> str:
        """Generate a markdown table without delta columns for cross-product data.

        Args:
            max_rows: Maximum number of rows to include
            include_delta: Whether to include delta columns (ignored for this table)
            comparison_data: Historical data for delta calculations (ignored for this table)
            comparison_period: Which comparison period to use (ignored for this table)

        Returns:
            Markdown table as a string
        """
        # Override to never include deltas for cross-product tables
        return super().generate_table(max_rows=max_rows, include_delta=False)


class HighestUseCountPerBladeTableGenerator(BaseTableGenerator):
    """Table generator for highest use count per blade in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get highest use count per blade data from aggregated data."""
        data = self.data.get("highest_use_count_per_blade", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] highest_use_count_per_blade data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] highest_use_count_per_blade record {i} is not a dict")
                continue

            # Check for required fields
            required_fields = ["user", "blade", "uses"]
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                if self.debug:
                    print(
                        f"[DEBUG] highest_use_count_per_blade record {i} missing fields: "
                        f"{missing_fields}"
                    )
                continue

            # Ensure uses is numeric and positive
            if not isinstance(record["uses"], (int, float)) or record["uses"] <= 0:
                if self.debug:
                    print(
                        f"[DEBUG] highest_use_count_per_blade record {i} has invalid uses: "
                        f"{record['uses']}"
                    )
                continue

            # Add a name field for delta calculations (combine user and blade)
            record_with_name = record.copy()
            record_with_name["name"] = f"{record['user']} - {record['blade']}"

            valid_data.append(record_with_name)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Highest Use Count per Blade"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the highest use count per blade table."""
        return {
            "user": {"display_name": "User"},
            "blade": {"display_name": "Blade"},
            "format": {"display_name": "Format"},
            "uses": {"display_name": "Uses", "format": "number"},
        }

    def generate_table(
        self,
        max_rows: int = 20,
        include_delta: bool = False,
        comparison_data: Optional[Dict[str, Any]] = None,
        comparison_period: str = "previous month",
    ) -> str:
        """Generate a markdown table without delta columns for cross-product data.

        Args:
            max_rows: Maximum number of rows to include
            include_delta: Whether to include delta columns (ignored for this table)
            comparison_data: Historical data for delta calculations (ignored for this table)
            comparison_period: Which comparison period to use (ignored for this table)

        Returns:
            Markdown table as a string
        """
        # Override to never include deltas for cross-product tables
        return super().generate_table(max_rows=max_rows, include_delta=False)
