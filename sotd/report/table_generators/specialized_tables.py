#!/usr/bin/env python3
"""Table generators for specialized hardware data in the hardware report."""

from typing import Any, Dict

from .base import BaseTableGenerator


class BlackbirdPlatesTableGenerator(BaseTableGenerator):
    """Table generator for Blackbird plates in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Blackbird plates data from aggregated data."""
        data = self.data.get("blackbird_plates", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] blackbird_plates data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] blackbird_plates record {i} is not a dict")
                continue

            plate = record.get("plate")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)

            if not plate:
                if self.debug:
                    print(f"[DEBUG] blackbird_plates record {i} missing plate field")
                continue

            valid_data.append(
                {
                    "plate": plate,
                    "uses": shaves,
                    "users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Blackbird plates records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Blackbird Plates"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "plate": {"display_name": "Plate", "format": "text"},
            "uses": {"display_name": "Uses", "format": "number"},
            "users": {"display_name": "Users", "format": "number"},
        }


class ChristopherBradleyPlatesTableGenerator(BaseTableGenerator):
    """Table generator for Christopher Bradley plates in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Christopher Bradley plates data from aggregated data."""
        data = self.data.get("christopher_bradley_plates", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] christopher_bradley_plates data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] christopher_bradley_plates record {i} is not a dict")
                continue

            plate = record.get("plate")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)

            if not plate:
                if self.debug:
                    print(f"[DEBUG] christopher_bradley_plates record {i} missing plate field")
                continue

            valid_data.append(
                {
                    "plate": plate,
                    "uses": shaves,
                    "users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Christopher Bradley plates records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Christopher Bradley Plates"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "plate": {"display_name": "Plate", "format": "text"},
            "uses": {"display_name": "Uses", "format": "number"},
            "users": {"display_name": "Users", "format": "number"},
        }


class GameChangerPlatesTableGenerator(BaseTableGenerator):
    """Table generator for Game Changer plates in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Game Changer plates data from aggregated data."""
        data = self.data.get("game_changer_plates", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] game_changer_plates data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] game_changer_plates record {i} is not a dict")
                continue

            plate = record.get("plate")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)

            if not plate:
                if self.debug:
                    print(f"[DEBUG] game_changer_plates record {i} missing plate field")
                continue

            valid_data.append(
                {
                    "plate": plate,
                    "uses": shaves,
                    "users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Game Changer plates records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Game Changer Plates"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "plate": {"display_name": "Plate", "format": "text"},
            "uses": {"display_name": "Uses", "format": "number"},
            "users": {"display_name": "Users", "format": "number"},
        }


class SuperSpeedTipsTableGenerator(BaseTableGenerator):
    """Table generator for Super Speed tips in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Super Speed tips data from aggregated data."""
        data = self.data.get("super_speed_tips", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] super_speed_tips data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] super_speed_tips record {i} is not a dict")
                continue

            tip = record.get("tip")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)

            if not tip:
                if self.debug:
                    print(f"[DEBUG] super_speed_tips record {i} missing tip field")
                continue

            valid_data.append(
                {
                    "tip": tip,
                    "uses": shaves,
                    "users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Super Speed tips records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Super Speed Tips"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "tip": {"display_name": "Tip", "format": "text"},
            "uses": {"display_name": "Uses", "format": "number"},
            "users": {"display_name": "Users", "format": "number"},
        }


class StraightRazorSpecsTableGenerator(BaseTableGenerator):
    """Table generator for straight razor specifications in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get straight razor specs data from aggregated data."""
        data = self.data.get("straight_razor_specs", [])

        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] straight_razor_specs data is not a list")
            return []

        # Validate each record has required fields
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] straight_razor_specs record {i} is not a dict")
                continue

            grind = record.get("grind")
            width = record.get("width")
            point = record.get("point")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)

            if not all([grind, width, point]):
                if self.debug:
                    print(f"[DEBUG] straight_razor_specs record {i} missing required fields")
                continue

            valid_data.append(
                {
                    "grind": grind,
                    "width": width,
                    "point": point,
                    "uses": shaves,
                    "users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid straight razor specs records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Straight Razor Specifications"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "grind": {"display_name": "Grind", "format": "text"},
            "width": {"display_name": "Width", "format": "text"},
            "point": {"display_name": "Point", "format": "text"},
            "uses": {"display_name": "Uses", "format": "number"},
            "users": {"display_name": "Users", "format": "number"},
        }
