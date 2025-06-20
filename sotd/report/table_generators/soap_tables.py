from typing import Any, Dict, List

from .base import (
    STANDARD_DIVERSITY_COLUMNS,
    ManufacturerTableGenerator,
    StandardProductTableGenerator,
)


class SoapMakersTableGenerator(ManufacturerTableGenerator):
    """Generates a table of soap makers with usage statistics."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get soap makers data from aggregated data."""
        data = self.data.get("soap_makers", [])
        return self._validate_data_records(data, "soap_makers", ["maker", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Soap Makers"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "maker"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Return column configuration for the soap makers table."""
        return {
            "maker": {"display_name": "name"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class SoapsTableGenerator(StandardProductTableGenerator):
    """Generates a table of soaps with usage statistics."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get soaps data from aggregated data."""
        data = self.data.get("soaps", [])
        return self._validate_data_records(data, "soaps", ["name", "shaves"])

    def get_table_title(self) -> str:
        """Return the table title."""
        return "Soaps"


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
        return STANDARD_DIVERSITY_COLUMNS

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "maker"
