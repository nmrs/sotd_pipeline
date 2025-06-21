#!/usr/bin/env python3
"""Table generators for specialized hardware data in the hardware report."""

from typing import Any

from .base import BaseTableGenerator, SpecializedTableGenerator


class BlackbirdPlatesTableGenerator(SpecializedTableGenerator):
    """Table generator for Blackbird plates in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Blackbird plates data from aggregated data."""
        data = self.data.get("blackbird_plates", [])
        valid_data = self._validate_data_records(data, "blackbird_plates", ["plate", "shaves"])

        if self.debug:
            print(f"[DEBUG] Found {len(valid_data)} valid Blackbird plates records")

        return valid_data

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Blackbird Plates"


class ChristopherBradleyPlatesTableGenerator(SpecializedTableGenerator):
    """Table generator for Christopher Bradley plates in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Christopher Bradley plates data from aggregated data."""
        data = self.data.get("christopher_bradley_plates", [])
        valid_data = self._validate_data_records(
            data, "christopher_bradley_plates", ["plate_type", "plate_level", "shaves"]
        )

        # Create combined plate identifier
        result = []
        for record in valid_data:
            plate_type = record.get("plate_type")
            plate_level = record.get("plate_level")
            if plate_type and plate_level:
                result.append(
                    {
                        "plate": f"{plate_type}{plate_level}",
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        if self.debug:
            print(f"[DEBUG] Found {len(result)} valid Christopher Bradley plates records")

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Christopher Bradley Plates"


class GameChangerPlatesTableGenerator(SpecializedTableGenerator):
    """Table generator for Game Changer plates in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Game Changer plates data from aggregated data."""
        data = self.data.get("game_changer_plates", [])
        valid_data = self._validate_data_records(data, "game_changer_plates", ["gap", "shaves"])

        # Map gap to plate field
        result = []
        for record in valid_data:
            gap = record.get("gap")
            if gap:
                result.append(
                    {
                        "plate": gap,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        if self.debug:
            print(f"[DEBUG] Found {len(result)} valid Game Changer plates records")

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Game Changer Plates"


class SuperSpeedTipsTableGenerator(SpecializedTableGenerator):
    """Table generator for Super Speed tips in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Super Speed tips data from aggregated data."""
        data = self.data.get("super_speed_tips", [])
        valid_data = self._validate_data_records(data, "super_speed_tips", ["tip", "shaves"])

        # Map tip to plate field
        result = []
        for record in valid_data:
            tip = record.get("tip")
            if tip:
                result.append(
                    {
                        "plate": tip,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        if self.debug:
            print(f"[DEBUG] Found {len(result)} valid Super Speed tips records")

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Super Speed Tips"


class StraightWidthsTableGenerator(SpecializedTableGenerator):
    """Table generator for straight razor widths in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get straight razor widths data from aggregated data."""
        data = self.data.get("straight_widths", [])
        valid_data = self._validate_data_records(data, "straight_widths", ["width", "shaves"])

        # Map width to plate field
        result = []
        for record in valid_data:
            width = record.get("width")
            if width:
                result.append(
                    {
                        "plate": width,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Straight Widths"


class StraightGrindsTableGenerator(SpecializedTableGenerator):
    """Table generator for straight razor grinds in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get straight razor grinds data from aggregated data."""
        data = self.data.get("straight_grinds", [])
        valid_data = self._validate_data_records(data, "straight_grinds", ["grind", "shaves"])

        # Map grind to plate field
        result = []
        for record in valid_data:
            grind = record.get("grind")
            if grind:
                result.append(
                    {
                        "plate": grind,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Straight Grinds"


class StraightPointsTableGenerator(SpecializedTableGenerator):
    """Table generator for straight razor points in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get straight razor points data from aggregated data."""
        data = self.data.get("straight_points", [])
        valid_data = self._validate_data_records(data, "straight_points", ["point", "shaves"])

        # Map point to plate field
        result = []
        for record in valid_data:
            point = record.get("point")
            if point:
                result.append(
                    {
                        "plate": point,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Straight Points"


# Factory method alternatives for simplified table creation
def create_blackbird_plates_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a Blackbird plates table using factory method."""
    return BaseTableGenerator.create_specialized_table(
        data=data,
        category="blackbird_plates",
        title="Blackbird Plates",
        name_key="plate",
        debug=debug,
    )


def create_christopher_bradley_plates_table(
    data: dict[str, Any], debug: bool = False
) -> BaseTableGenerator:
    """Create a Christopher Bradley plates table using factory method."""
    return BaseTableGenerator.create_specialized_table(
        data=data,
        category="christopher_bradley_plates",
        title="Christopher Bradley Plates",
        name_key="plate",
        debug=debug,
    )


def create_game_changer_plates_table(
    data: dict[str, Any], debug: bool = False
) -> BaseTableGenerator:
    """Create a Game Changer plates table using factory method."""
    return BaseTableGenerator.create_specialized_table(
        data=data,
        category="game_changer_plates",
        title="Game Changer Plates",
        name_key="plate",
        debug=debug,
    )


def create_super_speed_tips_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a Super Speed tips table using factory method."""
    return BaseTableGenerator.create_specialized_table(
        data=data,
        category="super_speed_tips",
        title="Super Speed Tips",
        name_key="plate",
        debug=debug,
    )


def create_straight_widths_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a straight widths table using factory method."""
    return BaseTableGenerator.create_specialized_table(
        data=data,
        category="straight_widths",
        title="Straight Widths",
        name_key="plate",
        debug=debug,
    )


def create_straight_grinds_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a straight grinds table using factory method."""
    return BaseTableGenerator.create_specialized_table(
        data=data,
        category="straight_grinds",
        title="Straight Grinds",
        name_key="plate",
        debug=debug,
    )


def create_straight_points_table(data: dict[str, Any], debug: bool = False) -> BaseTableGenerator:
    """Create a straight points table using factory method."""
    return BaseTableGenerator.create_specialized_table(
        data=data,
        category="straight_points",
        title="Straight Points",
        name_key="plate",
        debug=debug,
    )
