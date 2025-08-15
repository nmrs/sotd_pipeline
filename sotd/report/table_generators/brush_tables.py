#!/usr/bin/env python3
"""Table generators for brush-related data in the hardware report."""

from typing import Any

from .base import BaseTableGenerator, StandardProductTableGenerator


class BrushesTableGenerator(StandardProductTableGenerator):
    """Table generator for individual brushes in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brushes data from aggregated data."""
        data = self.data.get("brushes", [])
        return self._validate_data_records(data, "brushes", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brushes"


class BrushHandleMakersTableGenerator(StandardProductTableGenerator):
    """Table generator for brush handle makers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush handle maker data from aggregated data."""
        data = self.data.get("brush_handle_makers", [])
        return self._validate_data_records(data, "brush_handle_makers", ["handle_maker", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brush Handle Makers"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "handle_maker"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration with handle_maker mapped to name."""
        return {
            "handle_maker": {"display_name": "name"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class BrushKnotMakersTableGenerator(StandardProductTableGenerator):
    """Table generator for brush knot makers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush knot maker data from aggregated data."""
        data = self.data.get("brush_knot_makers", [])
        return self._validate_data_records(data, "brush_knot_makers", ["brand", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brush Knot Makers"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "brand"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration with brand mapped to name."""
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


class BrushFibersTableGenerator(StandardProductTableGenerator):
    """Table generator for brush fibers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush fiber data from aggregated data."""
        data = self.data.get("brush_fibers", [])
        valid_data = self._validate_data_records(data, "brush_fibers", ["fiber", "shaves"])

        # Normalize fiber names and merge duplicates
        fiber_counts = {}  # Track normalized fiber names and their counts

        for record in valid_data:
            # Normalize fiber name to title case
            normalized_fiber = record["fiber"].title()

            # Merge duplicate entries with same normalized name
            if normalized_fiber in fiber_counts:
                # Add to existing entry
                fiber_counts[normalized_fiber]["shaves"] += record["shaves"]
                fiber_counts[normalized_fiber]["unique_users"] += record.get("unique_users", 0)
                if self.debug:
                    print(
                        f"[DEBUG] Merged duplicate fiber: {record['fiber']} -> {normalized_fiber}"
                    )
            else:
                # Create new entry with normalized name
                new_record = record.copy()
                new_record["fiber"] = normalized_fiber
                fiber_counts[normalized_fiber] = new_record

        # Convert back to list
        result = list(fiber_counts.values())

        if self.debug:
            print(f"[DEBUG] Normalized {len(data)} fiber records to {len(result)} unique fibers")

        return result

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Knot Fibers"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "fiber"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration with fiber mapped to name."""
        return {
            "fiber": {"display_name": "name"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class BrushKnotSizesTableGenerator(StandardProductTableGenerator):
    """Table generator for brush knot sizes in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush knot size data from aggregated data."""
        data = self.data.get("brush_knot_sizes", [])
        valid_data = self._validate_data_records(
            data, "brush_knot_sizes", ["knot_size_mm", "shaves"]
        )

        # Filter invalid sizes
        filtered_data = []
        for record in valid_data:
            # Validate knot size is reasonable (15-50mm range)
            knot_size = record["knot_size_mm"]
            if not isinstance(knot_size, (int, float)):
                if self.debug:
                    print(f"[DEBUG] brush_knot_sizes record has non-numeric knot size: {knot_size}")
                continue

            if knot_size < 15 or knot_size > 50:
                if self.debug:
                    print(
                        f"[DEBUG] brush_knot_sizes record has invalid knot size: "
                        f"{knot_size}mm (outside 15-50mm range)"
                    )
                continue

            filtered_data.append(record)

        if self.debug:
            print(
                f"[DEBUG] Filtered {len(data)} knot size records to "
                f"{len(filtered_data)} valid sizes"
            )

        return filtered_data

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Knot Sizes"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "knot_size_mm"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration with knot_size_mm mapped to name."""
        return {
            "knot_size_mm": {"display_name": "name"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


# Factory method alternatives for simplified table creation
def create_brushes_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a brushes table generator."""
    return BrushesTableGenerator(data, debug)


def create_brush_handle_makers_table(
    data: dict[str, Any], debug: bool = False
) -> BaseTableGenerator:
    """Create a brush handle makers table generator."""
    return BrushHandleMakersTableGenerator(data, debug)


def create_brush_knot_makers_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a brush knot makers table generator."""
    return BrushKnotMakersTableGenerator(data, debug)


def create_brush_fibers_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a brush fibers table generator."""
    return BrushFibersTableGenerator(data, debug)


def create_brush_knot_sizes_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a brush knot sizes table generator."""
    return BrushKnotSizesTableGenerator(data, debug)
