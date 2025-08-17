from typing import Any

from .base import BaseTableGenerator, StandardProductTableGenerator


class RazorFormatsTableGenerator(StandardProductTableGenerator):
    """Table generator for razor formats in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor format data from aggregated data."""
        data = self.data.get("razor_formats", [])
        return self._validate_data_records(data, "razor_formats", ["format", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Razor Formats"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "format"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for razor formats table.

        Override to use 'format' field instead of 'name' field.
        """
        return {
            "format": {"display_name": "Format"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class RazorsTableGenerator(StandardProductTableGenerator):
    """Table generator for individual razors in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razors data from aggregated data."""
        data = self.data.get("razors", [])
        return self._validate_data_records(data, "razors", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Razors"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return custom column configuration with 'Razor' instead of 'Name'."""
        return {
            "name": {"display_name": "Razor"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class RazorManufacturersTableGenerator(StandardProductTableGenerator):
    """Table generator for razor manufacturers in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razor manufacturer data from aggregated data."""
        data = self.data.get("razor_manufacturers", [])
        return self._validate_data_records(data, "razor_manufacturers", ["brand", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Razor Manufacturers"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "brand"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Return column configuration for razor manufacturers table.

        Override to use 'brand' field instead of 'name' field.
        """
        return {
            "brand": {"display_name": "Manufacturer"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


# Factory method alternatives for simplified table creation
def create_razor_formats_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a razor formats table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data, category="razor_formats", title="Razor Formats", name_key="format", debug=debug
    )


def create_razors_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a razors table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data, category="razors", title="Razors", name_key="name", debug=debug
    )


def create_razor_manufacturers_table(
    data: dict[str, Any], debug: bool = False
) -> BaseTableGenerator:
    """Create a razor manufacturers table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data,
        category="razor_manufacturers",
        title="Razor Manufacturers",
        name_key="brand",
        debug=debug,
    )
