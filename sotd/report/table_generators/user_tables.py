#!/usr/bin/env python3
"""User table generators for the report phase."""

from typing import Any, Dict, List

from .base import BaseTableGenerator


class TopShaversTableGenerator(BaseTableGenerator):
    """Table generator for top shavers with tie-breaking logic."""

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table.

        Returns:
            List of user records with position, user, shaves, missed_days fields
        """
        if not self.data:
            return []

        # Get user data from aggregated data
        users_data = self.data.get("users", [])
        if not users_data:
            return []

        # Convert to list of dictionaries with required fields
        results = []
        for user_record in users_data:
            # Validate required fields
            if not all(key in user_record for key in ["user", "shaves", "missed_days"]):
                continue

            results.append(
                {
                    "position": user_record.get("position", 0),
                    "user": user_record["user"],  # for delta logic
                    "user_display": f"u/{user_record['user']}",  # for output
                    "shaves": user_record["shaves"],
                    "missed_days": user_record["missed_days"],
                }
            )

        return results

    def get_table_title(self) -> str:
        """Get the table title.

        Returns:
            Table title
        """
        return "Top Shavers"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table.

        Returns:
            Column configuration dictionary
        """
        return {
            "user_display": {
                "display_name": "user",
                "format": "text",
            },
            "shaves": {
                "display_name": "shaves",
                "format": "number",
            },
            "missed_days": {
                "display_name": "missed days",
                "format": "number",
            },
        }

    def get_name_key(self) -> str:
        """Get the key to use for matching items in delta calculations.

        Returns:
            Name key for delta calculations
        """
        return "user"

    def get_category_name(self) -> str:
        """Get the category name for this table generator.

        Returns:
            Category name for data matching
        """
        return "users"
