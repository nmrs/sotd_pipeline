from typing import Any, Dict, List

from .base import (
    BaseTableGenerator,
    StandardProductTableGenerator,
)
from .specialized_tables import DataTransformingTableGenerator


class SoapMakersTableGenerator(DataTransformingTableGenerator):
    """Generates a table of soap makers with usage statistics."""

    def _transform_soap_maker_data(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform soap maker data by mapping maker field to brand field.

        This method ensures consistent data transformation for both current and
        historical data in delta calculations.
        """
        transformed_record = record.copy()
        if "maker" in record:
            transformed_record["brand"] = record["maker"]
        return transformed_record

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get soap makers data from aggregated data."""
        data = self.data.get("soap_makers", [])
        # Filter for brands with 5+ shaves (as requested by user)
        filtered_data = [
            item for item in data if item.get("shaves", 0) >= 5
        ]
        validated_data = self._validate_data_records(
            filtered_data, "soap_makers", ["maker", "shaves"]
        )

        # Transform maker field to brand field to work with STANDARD_MANUFACTURER_COLUMNS
        transformed_data = []
        for record in validated_data:
            transformed_data.append(self._transform_soap_maker_data(record))

        return transformed_data

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
        return "brand"  # Changed from "maker" to "brand" to match transformed data

    def _get_category_name(self) -> str:
        """Get the category name for this table generator."""
        return "soap_makers"

    def _get_source_field(self) -> str:
        """Get the source field name in historical data."""
        return "maker"

    def _get_target_field(self) -> str:
        """Get the target field name in current data."""
        return "brand"

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all soap makers."""
        return False


class SoapsTableGenerator(StandardProductTableGenerator):
    """Generates a table of soaps with usage statistics."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get soaps data from aggregated data."""
        data = self.data.get("soaps", [])
        # Filter for soaps with 5+ shaves (as requested by user)
        filtered_data = [item for item in data if item.get("shaves", 0) >= 5]
        return self._validate_data_records(filtered_data, "soaps", ["name", "shaves"])

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

    def should_limit_rows(self) -> bool:
        """Disable row limiting to show all soaps."""
        return False


class BrandDiversityTableGenerator(StandardProductTableGenerator):
    """Generates a table showing brand diversity (number of unique soaps per maker)."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get brand diversity data from aggregated data."""
        data = self.data.get("brand_diversity", [])
        # Filter for brands with 5+ unique soaps (as requested by user)
        filtered_data = [
            item for item in data if item.get("unique_soaps", 0) >= 5
        ]
        return self._validate_data_records(
            filtered_data, "brand_diversity", ["maker", "unique_soaps"]
        )

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

    def get_category_name(self) -> str:
        """Get the category name for this table generator."""
        return "brand_diversity"

    def _get_category_name(self) -> str:
        """Get the category name for this table generator."""
        return "brand_diversity"

    def _get_source_field(self) -> str:
        """Get the source field name in historical data."""
        return "maker"

    def _get_target_field(self) -> str:
        """Get the target field name in current data."""
        return "maker"

    def should_limit_rows(self) -> bool:
        """Disable row limiting since we want to show all brands that meet the 5+ threshold."""
        return False


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
