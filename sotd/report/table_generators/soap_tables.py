from typing import Any, Dict, List

from .base import (
    BaseTableGenerator,
    StandardProductTableGenerator,
)


class SoapMakersTableGenerator(StandardProductTableGenerator):
    """Generates a table of soap makers with usage statistics."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get soap makers data from aggregated data."""
        data = self.data.get("soap_makers", [])
        return self._validate_data_records(data, "soap_makers", ["maker", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Soap Makers"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Return column configuration for soap makers table."""
        from .base import STANDARD_MANUFACTURER_COLUMNS

        # Override to use "Brand" instead of "Manufacturer"
        config = STANDARD_MANUFACTURER_COLUMNS.copy()
        config["brand"]["display_name"] = "Brand"
        return config

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "maker"


class SoapsTableGenerator(StandardProductTableGenerator):
    """Generates a table of soaps with usage statistics."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get soaps data from aggregated data."""
        data = self.data.get("soaps", [])
        return self._validate_data_records(data, "soaps", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Soaps"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Return column configuration for soaps table."""
        from .base import STANDARD_PRODUCT_COLUMNS

        # Override to use "Soap" instead of "Razor"
        config = STANDARD_PRODUCT_COLUMNS.copy()
        config["name"]["display_name"] = "Soap"
        return config


class BrandDiversityTableGenerator(StandardProductTableGenerator):
    """Generates a table showing brand diversity (number of unique soaps per maker)."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get brand diversity data from aggregated data."""
        soaps = self.data.get("soaps", [])
        # Extract maker from soap name (assume first word is maker)
        diversity: Dict[str, int] = {}
        for s in soaps:
            if "name" in s and s["name"]:
                maker = s["name"].split()[0]
                diversity[maker] = diversity.get(maker, 0) + 1
        # Convert to list of dicts
        return [
            {"maker": maker, "unique_soaps": count}
            for maker, count in sorted(diversity.items(), key=lambda x: x[1], reverse=True)
        ]

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Brand Diversity (Unique Soaps per Maker)"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Return column configuration for the brand diversity table."""
        from .base import STANDARD_DIVERSITY_COLUMNS

        # Override to use "Brand" instead of "Maker"
        config = STANDARD_DIVERSITY_COLUMNS.copy()
        config["maker"]["display_name"] = "Brand"
        return config

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "maker"


# Factory method alternatives for simplified table creation
def create_soap_makers_table(data: Dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a soap makers table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data, category="soap_makers", title="Soap Makers", name_key="maker", debug=debug
    )


def create_soaps_table(data: Dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a soaps table using factory method."""
    return BaseTableGenerator.create_standard_product_table(
        data=data, category="soaps", title="Soaps", name_key="name", debug=debug
    )


def create_brand_diversity_table(data: Dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a brand diversity table using factory method."""
    return BaseTableGenerator.create_diversity_table(
        data=data,
        category="brand_diversity",
        title="Brand Diversity (Unique Soaps per Maker)",
        name_key="maker",
        debug=debug,
    )
