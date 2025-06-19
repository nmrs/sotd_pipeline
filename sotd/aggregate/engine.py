"""Core aggregation engine using pandas for efficient data processing."""

# Import core aggregation functions
from sotd.aggregate.aggregation_functions import calculate_basic_metrics, filter_matched_records

# Import specialized aggregators
from sotd.aggregate.engine_specialized import (
    aggregate_blackbird_plates,
    aggregate_blade_manufacturers,
    aggregate_brush_fibers,
    aggregate_brush_handle_makers,
    aggregate_brush_knot_makers,
    aggregate_brush_knot_sizes,
    aggregate_christopher_bradley_plates,
    aggregate_game_changer_plates,
    aggregate_razor_blade_combinations,
    aggregate_razor_manufacturers,
    aggregate_soap_makers,
    aggregate_straight_razor_specs,
    aggregate_super_speed_tips,
)

# Import product aggregators
from sotd.aggregate.product_aggregators import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)

# Import user aggregators
from sotd.aggregate.user_aggregators import aggregate_user_blade_usage, aggregate_users

# Re-export all functions for backward compatibility
__all__ = [
    # Core functions
    "calculate_basic_metrics",
    "filter_matched_records",
    # Product aggregators
    "aggregate_razors",
    "aggregate_blades",
    "aggregate_soaps",
    "aggregate_brushes",
    # User aggregators
    "aggregate_users",
    "aggregate_user_blade_usage",
    # Specialized aggregators
    "aggregate_razor_manufacturers",
    "aggregate_blade_manufacturers",
    "aggregate_soap_makers",
    "aggregate_brush_knot_makers",
    "aggregate_brush_handle_makers",
    "aggregate_brush_fibers",
    "aggregate_brush_knot_sizes",
    "aggregate_blackbird_plates",
    "aggregate_christopher_bradley_plates",
    "aggregate_game_changer_plates",
    "aggregate_super_speed_tips",
    "aggregate_straight_razor_specs",
    "aggregate_razor_blade_combinations",
]
