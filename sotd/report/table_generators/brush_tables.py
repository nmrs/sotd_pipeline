#!/usr/bin/env python3
"""Table generators for brush-related data in the hardware report."""

from typing import Any

from .base import BaseTableGenerator, StandardProductTableGenerator


class BrushesTableGenerator(StandardProductTableGenerator):
    """Table generator for individual brushes in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brushes data from aggregated data."""
        data = self.data.get("brushes", [])
        # No filtering - show all brushes as template doesn't specify limits
        return self._validate_data_records(data, "brushes", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brushes"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return custom column configuration with 'Brush' instead of 'Name'."""
        return {
            "rank": {"display_name": "Rank"},
            "name": {"display_name": "Brush"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all brushes."""
        return False


class BrushHandleMakersTableGenerator(StandardProductTableGenerator):
    """Table generator for brush handle makers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush handle maker data from aggregated data."""
        data = self.data.get("brush_handle_makers", [])
        # No filtering - show all makers as template doesn't specify limits
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
            "rank": {"display_name": "Rank"},
            "handle_maker": {"display_name": "Maker"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all makers."""
        return False


class BrushKnotMakersTableGenerator(StandardProductTableGenerator):
    """Table generator for brush knot makers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush knot maker data from aggregated data."""
        data = self.data.get("brush_knot_makers", [])
        # No filtering - show all makers as template doesn't specify limits
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
            "rank": {"display_name": "Rank"},
            "brand": {"display_name": "Maker"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all makers."""
        return False


class BrushFibersTableGenerator(StandardProductTableGenerator):
    """Table generator for brush fibers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush fibers data from aggregated data."""
        data = self.data.get("brush_fibers", [])
        # No filtering - show all fibers as template doesn't specify limits
        return self._validate_data_records(data, "brush_fibers", ["fiber", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Knot Fibers"

    def get_category_name(self) -> str:
        """Return the category name for data matching in delta calculations."""
        return "brush_fibers"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "fiber"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration with fiber mapped to name."""
        return {
            "rank": {"display_name": "Rank"},
            "fiber": {"display_name": "Fiber"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all fibers."""
        return False


class BrushKnotSizesTableGenerator(StandardProductTableGenerator):
    """Table generator for brush knot sizes in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get brush knot sizes data from aggregated data."""
        data = self.data.get("brush_knot_sizes", [])
        # No filtering - show all sizes as template doesn't specify limits
        return self._validate_data_records(data, "brush_knot_sizes", ["knot_size_mm", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Knot Sizes"

    def get_category_name(self) -> str:
        """Return the category name for data matching in delta calculations."""
        return "brush_knot_sizes"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "knot_size_mm"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration with custom knot size formatting."""
        return {
            "rank": {"display_name": "Rank"},
            "knot_size_mm": {"display_name": "Size", "format": "smart_decimal", "decimals": 1},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all sizes."""
        return False


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
