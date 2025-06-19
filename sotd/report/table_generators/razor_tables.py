from typing import Any

from .base import BaseTableGenerator


class RazorFormatsTableGenerator(BaseTableGenerator):
    """Table generator for razor formats in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor format data from aggregated data."""
        # Defensive: aggregated data should have 'razor_formats' key
        data = self.data.get("razor_formats", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] razor_formats data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] razor_formats record {i} is not a dict")
                continue

            # Check for required fields
            if "format" not in record or "count" not in record:
                if self.debug:
                    print(f"[DEBUG] razor_formats record {i} missing required fields")
                continue

            # Ensure count is numeric
            if not isinstance(record["count"], (int, float)) or record["count"] <= 0:
                if self.debug:
                    print(f"[DEBUG] razor_formats record {i} has invalid count: {record['count']}")
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Razor Formats"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the razor formats table."""
        return {
            "format": {"display_name": "Format"},
            "count": {"display_name": "Uses", "format": "number"},
            "percent": {"display_name": "% of Shaves", "format": "decimal", "decimals": 1},
        }


class RazorsTableGenerator(BaseTableGenerator):
    """Table generator for individual razors in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razors data from aggregated data."""
        data = self.data.get("razors", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] razors data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] razors record {i} is not a dict")
                continue

            # Check for required fields - real data has 'name', 'shaves', 'unique_users'
            required_fields = ["name", "shaves"]
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                if self.debug:
                    print(f"[DEBUG] razors record {i} missing fields: {missing_fields}")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(f"[DEBUG] razors record {i} has invalid shaves: {record['shaves']}")
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Razors"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the razors table."""
        return {
            "name": {"display_name": "Razor"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }


class RazorManufacturersTableGenerator(BaseTableGenerator):
    """Table generator for razor manufacturers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor manufacturer data from aggregated data."""
        data = self.data.get("razor_manufacturers", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] razor_manufacturers data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] razor_manufacturers record {i} is not a dict")
                continue

            # Check for required fields
            if "brand" not in record or "shaves" not in record:
                if self.debug:
                    print(f"[DEBUG] razor_manufacturers record {i} missing required fields")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(
                        f"[DEBUG] razor_manufacturers record {i} has invalid shaves: "
                        f"{record['shaves']}"
                    )
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Razor Manufacturers"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the razor manufacturers table."""
        return {
            "brand": {"display_name": "Brand"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }
