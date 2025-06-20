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
                    "shaves": shaves,
                    "unique_users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Blackbird plates records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Blackbird Plates"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "plate"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "plate": {"display_name": "Plate", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
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

            plate_type = record.get("plate_type")
            plate_level = record.get("plate_level")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)

            if not plate_type or not plate_level:
                if self.debug:
                    print(
                        f"[DEBUG] christopher_bradley_plates record {i} missing "
                        f"plate_type or plate_level field"
                    )
                continue

            # Create a combined plate identifier
            plate = f"{plate_type}{plate_level}"

            valid_data.append(
                {
                    "plate": plate,
                    "shaves": shaves,
                    "unique_users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Christopher Bradley plates records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Christopher Bradley Plates"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "plate"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "plate": {"display_name": "Plate", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
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

            gap = record.get("gap")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)

            if not gap:
                if self.debug:
                    print(f"[DEBUG] game_changer_plates record {i} missing gap field")
                continue

            valid_data.append(
                {
                    "plate": gap,
                    "shaves": shaves,
                    "unique_users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Game Changer plates records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Game Changer Plates"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "plate"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "plate": {"display_name": "Plate", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
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
                    "shaves": shaves,
                    "unique_users": unique_users,
                }
            )

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Super Speed tips records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Super Speed Tips"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "tip"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        return {
            "tip": {"display_name": "Tip", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class StraightWidthsTableGenerator(BaseTableGenerator):
    """Table generator for straight razor widths in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        data = self.data.get("straight_widths", [])
        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] straight_widths data is not a list")
            return []
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] straight_widths record {i} is not a dict")
                continue
            width = record.get("width")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)
            if not width:
                if self.debug:
                    print(f"[DEBUG] straight_widths record {i} missing width field")
                continue
            valid_data.append(
                {
                    "name": width,
                    "shaves": shaves,
                    "unique_users": unique_users,
                }
            )
        return valid_data

    def get_table_title(self) -> str:
        return "Straight Widths"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "name"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        return {
            "name": {"display_name": "Width", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class StraightGrindsTableGenerator(BaseTableGenerator):
    """Table generator for straight razor grinds in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        data = self.data.get("straight_grinds", [])
        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] straight_grinds data is not a list")
            return []
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] straight_grinds record {i} is not a dict")
                continue
            grind = record.get("grind")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)
            if not grind:
                if self.debug:
                    print(f"[DEBUG] straight_grinds record {i} missing grind field")
                continue
            valid_data.append(
                {
                    "name": grind,
                    "shaves": shaves,
                    "unique_users": unique_users,
                }
            )
        return valid_data

    def get_table_title(self) -> str:
        return "Straight Grinds"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "name"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        return {
            "name": {"display_name": "Grind", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }


class StraightPointsTableGenerator(BaseTableGenerator):
    """Table generator for straight razor points in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        data = self.data.get("straight_points", [])
        if not isinstance(data, list):
            if self.debug:
                print("[DEBUG] straight_points data is not a list")
            return []
        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] straight_points record {i} is not a dict")
                continue
            point = record.get("point")
            shaves = record.get("shaves", 0)
            unique_users = record.get("unique_users", 0)
            if not point:
                if self.debug:
                    print(f"[DEBUG] straight_points record {i} missing point field")
                continue
            valid_data.append(
                {
                    "name": point,
                    "shaves": shaves,
                    "unique_users": unique_users,
                }
            )
        return valid_data

    def get_table_title(self) -> str:
        return "Straight Points"

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "name"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        return {
            "name": {"display_name": "Point", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }
