#!/usr/bin/env python3
"""Table generators for brush-related data in the hardware report."""

from typing import Any

from .base import BaseTableGenerator


class BrushesTableGenerator(BaseTableGenerator):
    """Table generator for individual brushes in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brushes data from aggregated data."""
        data = self.data.get("brushes", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] brushes data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] brushes record {i} is not a dict")
                continue

            # Check for required fields - real data has 'name', 'shaves', 'unique_users'
            required_fields = ["name", "shaves"]
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                if self.debug:
                    print(f"[DEBUG] brushes record {i} missing fields: {missing_fields}")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(f"[DEBUG] brushes record {i} has invalid shaves: {record['shaves']}")
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brushes"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the brushes table."""
        return {
            "name": {"display_name": "Brush"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }


class BrushHandleMakersTableGenerator(BaseTableGenerator):
    """Table generator for brush handle makers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush handle maker data from aggregated data."""
        data = self.data.get("brush_handle_makers", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] brush_handle_makers data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] brush_handle_makers record {i} is not a dict")
                continue

            # Check for required fields
            if "handle_maker" not in record or "shaves" not in record:
                if self.debug:
                    print(f"[DEBUG] brush_handle_makers record {i} missing required fields")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(
                        f"[DEBUG] brush_handle_makers record {i} has invalid shaves: "
                        f"{record['shaves']}"
                    )
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brush Handle Makers"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the brush handle makers table."""
        return {
            "handle_maker": {"display_name": "Handle Maker"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }


class BrushKnotMakersTableGenerator(BaseTableGenerator):
    """Table generator for brush knot makers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush knot maker data from aggregated data."""
        data = self.data.get("brush_knot_makers", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] brush_knot_makers data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] brush_knot_makers record {i} is not a dict")
                continue

            # Check for required fields
            if "brand" not in record or "shaves" not in record:
                if self.debug:
                    print(f"[DEBUG] brush_knot_makers record {i} missing required fields")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(
                        f"[DEBUG] brush_knot_makers record {i} has invalid shaves: "
                        f"{record['shaves']}"
                    )
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brush Knot Makers"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the brush knot makers table."""
        return {
            "brand": {"display_name": "Knot Maker"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }


class BrushFibersTableGenerator(BaseTableGenerator):
    """Table generator for brush fibers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush fiber data from aggregated data."""
        data = self.data.get("brush_fibers", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] brush_fibers data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] brush_fibers record {i} is not a dict")
                continue

            # Check for required fields
            if "fiber" not in record or "shaves" not in record:
                if self.debug:
                    print(f"[DEBUG] brush_fibers record {i} missing required fields")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(f"[DEBUG] brush_fibers record {i} has invalid shaves: {record['shaves']}")
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brush Fibers"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the brush fibers table."""
        return {
            "fiber": {"display_name": "Fiber"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }


class BrushKnotSizesTableGenerator(BaseTableGenerator):
    """Table generator for brush knot sizes in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush knot size data from aggregated data."""
        data = self.data.get("brush_knot_sizes", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] brush_knot_sizes data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] brush_knot_sizes record {i} is not a dict")
                continue

            # Check for required fields
            if "knot_size_mm" not in record or "shaves" not in record:
                if self.debug:
                    print(f"[DEBUG] brush_knot_sizes record {i} missing required fields")
                continue

            # Ensure shaves is numeric and positive
            if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                if self.debug:
                    print(
                        f"[DEBUG] brush_knot_sizes record {i} has invalid shaves: "
                        f"{record['shaves']}"
                    )
                continue

            valid_data.append(record)

        return valid_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brush Knot Sizes"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for the brush knot sizes table."""
        return {
            "knot_size_mm": {"display_name": "Knot Size (mm)"},
            "shaves": {"display_name": "Uses", "format": "number"},
            "unique_users": {"display_name": "Users", "format": "number"},
        }
