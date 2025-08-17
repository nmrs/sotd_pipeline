#!/usr/bin/env python3
"""Table generators for specialized hardware data in the hardware report."""

from typing import Any, Dict, List

from sotd.report.table_generators.base import BaseTableGenerator, SpecializedTableGenerator


class DataTransformingTableGenerator(SpecializedTableGenerator):
    """Base class for specialized table generators that need data transformation for delta
    calculations.

    This class handles the common pattern where specialized generators transform data
    structure in get_table_data() but need to apply the same transformation to historical
    data for deltas.
    """

    def _transform_historical_data_for_deltas(
        self, historical_data: list[dict[str, Any]], source_field: str, target_field: str
    ) -> list[dict[str, Any]]:
        """Transform historical data to match current data structure for delta calculations.

        Args:
            historical_data: Historical data records
            source_field: The field name in historical data (e.g., "grind", "point", "width")
            target_field: The field name in current data (e.g., "grind", "point", "width")

        Returns:
            Transformed historical data with consistent field names
        """
        transformed_data = []
        for record in historical_data:
            source_value = record.get(source_field)
            if source_value is not None and source_value != "":
                transformed_record = record.copy()
                transformed_record[target_field] = source_value
                transformed_data.append(transformed_record)

        if self.debug:
            print(
                f"[DEBUG] Transformed {len(historical_data)} historical records from "
                f"'{source_field}' to '{target_field}' for delta calculation"
            )

        return transformed_data

    def _calculate_multi_period_deltas(
        self,
        current_data: List[Dict[str, Any]],
        comparison_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Calculate deltas for the current data across multiple periods.

        Override to transform historical data to match current data structure.
        """
        if not comparison_data:
            if self.debug:
                print("[DEBUG] No comparison data provided for delta calculation")
            return current_data

        # Start with the current data
        result = current_data.copy()

        # Calculate deltas for each period and add to the result
        for period, (metadata, historical_data) in comparison_data.items():
            if self.debug:
                print(f"[DEBUG] Calculating deltas for period: {period}")

            # Get the category data for this period
            category = self._get_category_name()
            historical_category_data = historical_data.get(category, [])

            if not historical_category_data:
                if self.debug:
                    print(f"[DEBUG] No historical data found for category: {category}")
                continue

            if self.debug:
                print(
                    f"[DEBUG] Found {len(historical_category_data)} historical records "
                    f"for category: {category}"
                )

            # Transform historical data to match current data structure
            transformed_historical_data = self._transform_historical_data_for_deltas(
                historical_category_data, self._get_source_field(), self._get_target_field()
            )

            # Add positions to transformed historical data if not present
            if not any("position" in item for item in transformed_historical_data):
                transformed_historical_data = self._add_positions(
                    transformed_historical_data, self._get_target_field()
                )
                if self.debug:
                    print("[DEBUG] Added positions to transformed historical data")
            else:
                if self.debug:
                    print("[DEBUG] Positions already exist in transformed historical data")

            # Calculate deltas for this period using transformed data
            deltas = self.delta_calculator.calculate_deltas(
                current_data,
                transformed_historical_data,
                name_key=self._get_target_field(),
                max_items=len(current_data),
            )

            # Add delta information to the result
            for i, delta in enumerate(deltas):
                if i < len(result):
                    # Add just the delta value that the base table generator expects
                    # Use the same key format as _add_multi_period_delta_column_config
                    period_key = period.lower().replace(" ", "_").replace("-", "_")
                    result[i][f"delta_{period_key}"] = delta.get("delta_text", "n/a")

            if self.debug:
                print(f"[DEBUG] Added deltas for period {period}")

        if self.debug:
            print(f"[DEBUG] Calculated multi-period deltas for {len(result)} items")

        return result

    def get_category_name(self) -> str:
        """Get the category name for this table generator.

        Override to return the specific category name for data matching.
        """
        return self._get_category_name()

    def get_name_key(self) -> str:
        """Get the key to use for matching items in delta calculations.

        Override to return the target field name for matching.
        """
        return self._get_target_field()

    def _get_category_name(self) -> str:
        """Get the category name for this table generator. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _get_category_name")

    def _get_source_field(self) -> str:
        """Get the source field name in historical data. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _get_source_field")

    def _get_target_field(self) -> str:
        """Get the target field name in current data. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _get_target_field")


class BlackbirdPlatesTableGenerator(DataTransformingTableGenerator):
    """Table generator for Blackbird plates in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Blackbird plates data from aggregated data."""
        data = self.data.get("blackbird_plates", [])
        valid_data = self._validate_data_records(data, "blackbird_plates", ["plate", "shaves"])

        # Map plate to plate field (no transformation needed, just validation)
        result = []
        for record in valid_data:
            plate = record.get("plate")
            if plate:
                result.append(
                    {
                        "plate": plate,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Blackbird Plates"

    def _get_category_name(self) -> str:
        return "blackbird_plates"

    def _get_source_field(self) -> str:
        return "plate"

    def _get_target_field(self) -> str:
        return "plate"


class ChristopherBradleyPlatesTableGenerator(DataTransformingTableGenerator):
    """Table generator for Christopher Bradley plates in the hardware report."""

    def _transform_plate_data(self, record: dict[str, Any]) -> dict[str, Any]:
        """Transform plate data by combining plate_type + plate_level into plate field.

        This method ensures consistent data transformation for both current and
        historical data. For SB plates, shows just the plate level (e.g., "D", "C",
        "B", "AA"). For OC plates, shows "OC-[plate]" format (e.g., "OC-F").
        """
        plate_type = record.get("plate_type")
        plate_level = record.get("plate_level")
        if plate_type and plate_level:
            # Format plate name based on type
            if plate_type == "SB":
                # For SB plates, show just the plate level
                plate_name = plate_level
            elif plate_type == "OC":
                # For OC plates, show "OC-[plate]" format
                plate_name = f"OC-{plate_level}"
            else:
                # Fallback for any other plate types
                plate_name = f"{plate_type}{plate_level}"

            return {
                "plate": plate_name,
                "shaves": record.get("shaves", 0),
                "unique_users": record.get("unique_users", 0),
            }
        return {}

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get Christopher Bradley plates data from aggregated data."""
        data = self.data.get("christopher_bradley_plates", [])
        valid_data = self._validate_data_records(
            data, "christopher_bradley_plates", ["plate_type", "plate_level", "shaves"]
        )

        # Use unified transformation method
        result = []
        for record in valid_data:
            transformed_record = self._transform_plate_data(record)
            if transformed_record:
                result.append(transformed_record)

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Christopher Bradley Plates"

    def _get_category_name(self) -> str:
        return "christopher_bradley_plates"

    def _get_source_field(self) -> str:
        return "plate_type"

    def _get_target_field(self) -> str:
        return "plate"

    def _transform_historical_data_for_deltas(
        self, historical_data: list[dict[str, Any]], source_field: str, target_field: str
    ) -> list[dict[str, Any]]:
        """Override to use unified transformation logic for Christopher Bradley plates.

        This ensures historical data is transformed exactly like current data.
        """
        transformed_data = []
        for record in historical_data:
            transformed_record = self._transform_plate_data(record)
            if transformed_record:
                transformed_data.append(transformed_record)

        if self.debug:
            print(
                f"[DEBUG] Transformed {len(historical_data)} historical records using "
                f"unified plate transformation logic"
            )

        return transformed_data


class GameChangerPlatesTableGenerator(DataTransformingTableGenerator):
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

    def _get_category_name(self) -> str:
        return "game_changer_plates"

    def _get_source_field(self) -> str:
        return "gap"

    def _get_target_field(self) -> str:
        return "plate"


class SuperSpeedTipsTableGenerator(DataTransformingTableGenerator):
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

    def _get_category_name(self) -> str:
        return "super_speed_tips"

    def _get_source_field(self) -> str:
        return "tip"

    def _get_target_field(self) -> str:
        return "plate"


class StraightWidthsTableGenerator(DataTransformingTableGenerator):
    """Table generator for straight razor widths in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get straight razor widths data from aggregated data."""
        data = self.data.get("straight_widths", [])
        valid_data = self._validate_data_records(data, "straight_widths", ["width", "shaves"])

        # Map width to width field (no transformation needed, just validation)
        result = []
        for record in valid_data:
            width = record.get("width")
            if width:
                result.append(
                    {
                        "width": width,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Straight Widths"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Get column configuration with width field mapped to name."""
        return {
            "width": {"display_name": "Width", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def _get_category_name(self) -> str:
        return "straight_widths"

    def _get_source_field(self) -> str:
        return "width"

    def _get_target_field(self) -> str:
        return "width"


class StraightGrindsTableGenerator(DataTransformingTableGenerator):
    """Table generator for straight razor grinds in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get straight razor grinds data from aggregated data."""
        data = self.data.get("straight_grinds", [])
        valid_data = self._validate_data_records(data, "straight_grinds", ["grind", "shaves"])

        # Map grind to grind field (no transformation needed, just validation)
        result = []
        for record in valid_data:
            grind = record.get("grind")
            if grind:
                result.append(
                    {
                        "grind": grind,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Straight Grinds"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Get column configuration with grind field mapped to name."""
        return {
            "grind": {"display_name": "Grind", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def _get_category_name(self) -> str:
        return "straight_grinds"

    def _get_source_field(self) -> str:
        return "grind"

    def _get_target_field(self) -> str:
        return "grind"


class StraightPointsTableGenerator(DataTransformingTableGenerator):
    """Table generator for straight razor points in the hardware report."""

    def get_table_data(self) -> list[dict[str, Any]]:
        """Get straight razor points data from aggregated data."""
        data = self.data.get("straight_points", [])
        valid_data = self._validate_data_records(data, "straight_points", ["point", "shaves"])

        # Map point to point field (no transformation needed, just validation)
        result = []
        for record in valid_data:
            point = record.get("point")
            if point:
                result.append(
                    {
                        "point": point,
                        "shaves": record.get("shaves", 0),
                        "unique_users": record.get("unique_users", 0),
                    }
                )

        return result

    def get_table_title(self) -> str:
        """Get the table title."""
        return "Straight Points"

    def get_column_config(self) -> dict[str, dict[str, Any]]:
        """Get column configuration with point field mapped to name."""
        return {
            "point": {"display_name": "Point", "format": "text"},
            "shaves": {"display_name": "shaves", "format": "number"},
            "unique_users": {"display_name": "unique users", "format": "number"},
            "avg_shaves_per_user": {
                "display_name": "avg shaves per user",
                "format": "decimal",
                "decimals": 2,
            },
        }

    def _get_category_name(self) -> str:
        return "straight_points"

    def _get_source_field(self) -> str:
        return "point"

    def _get_target_field(self) -> str:
        return "point"


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
