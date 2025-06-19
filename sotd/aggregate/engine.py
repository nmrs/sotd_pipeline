#!/usr/bin/env python3
"""Core aggregation engine using pandas for efficient data processing."""

# Import core aggregation functions
from sotd.aggregate.aggregation_functions import calculate_basic_metrics, filter_matched_records

# Import specialized aggregators
from sotd.aggregate.blackbird_plate_aggregator import aggregate_blackbird_plates

# Import product aggregators
from sotd.aggregate.blade_aggregator import aggregate_blades
from sotd.aggregate.brush_aggregator import aggregate_brushes
from sotd.aggregate.christopher_bradley_plate_aggregator import aggregate_christopher_bradley_plates
from sotd.aggregate.fiber_aggregator import aggregate_brush_fibers
from sotd.aggregate.game_changer_plate_aggregator import aggregate_game_changer_plates
from sotd.aggregate.handle_maker_aggregator import aggregate_brush_handle_makers
from sotd.aggregate.knot_maker_aggregator import aggregate_brush_knot_makers
from sotd.aggregate.knot_size_aggregator import aggregate_brush_knot_sizes
from sotd.aggregate.razor_aggregator import aggregate_razors
from sotd.aggregate.razor_blade_combo_aggregator import aggregate_razor_blade_combinations
from sotd.aggregate.razor_format_aggregator import aggregate_razor_formats
from sotd.aggregate.soap_aggregator import aggregate_soaps
from sotd.aggregate.soap_maker_aggregator import aggregate_soap_makers
from sotd.aggregate.straight_razor_spec_aggregator import aggregate_straight_razor_specs
from sotd.aggregate.super_speed_tip_aggregator import aggregate_super_speed_tips
from sotd.aggregate.user_aggregator import aggregate_users

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
    # Specialized aggregators
    "aggregate_razor_formats",
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
