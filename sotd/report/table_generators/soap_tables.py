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
            "maker": {"display_name": "name"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
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
            "name": {"display_name": "name"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
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
            "maker": {"display_name": "name"},
            "unique_soaps": {"display_name": "unique soaps", "format": "number"},
        }
