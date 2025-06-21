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


class RazorsTableGenerator(StandardProductTableGenerator):
    """Table generator for individual razors in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get razors data from aggregated data."""
        data = self.data.get("razors", [])
        return self._validate_data_records(data, "razors", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Razors"


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
