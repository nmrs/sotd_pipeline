from typing import Any, Dict, List

from .base import BaseTableGenerator


class SoapMakersTableGenerator(BaseTableGenerator):
    """Generates a table of soap makers with usage statistics."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        return self.data.get("soap_makers", [])

    def get_table_title(self) -> str:
        return "Soap Makers"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        return {
            "maker": {"display_name": "Maker"},
            "shaves": {"display_name": "Shaves", "format": "number"},
            "unique_users": {"display_name": "Unique Users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "Avg Shaves/User",
                "format": "decimal",
                "decimals": 2,
            },
        }


class SoapsTableGenerator(BaseTableGenerator):
    """Generates a table of soaps with usage statistics."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        return self.data.get("soaps", [])

    def get_table_title(self) -> str:
        return "Soaps"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        return {
            "name": {"display_name": "Soap"},
            "shaves": {"display_name": "Shaves", "format": "number"},
            "unique_users": {"display_name": "Unique Users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "Avg Shaves/User",
                "format": "decimal",
                "decimals": 2,
            },
        }


class BrandDiversityTableGenerator(BaseTableGenerator):
    """Generates a table showing brand diversity (number of unique soaps per maker)."""

    def get_table_data(self) -> List[Dict[str, Any]]:
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
        return "Brand Diversity (Unique Soaps per Maker)"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        return {
            "maker": {"display_name": "Maker"},
            "unique_soaps": {"display_name": "Unique Soaps", "format": "number"},
        }
