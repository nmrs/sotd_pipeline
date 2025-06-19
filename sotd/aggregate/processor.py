#!/usr/bin/env python3
"""Data processing logic for the aggregate phase."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from sotd.aggregate.aggregation_functions import calculate_basic_metrics, filter_matched_records
from sotd.aggregate.engine import (
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
from sotd.aggregate.load import get_enriched_file_path, load_enriched_data
from sotd.aggregate.product_aggregators import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)
from sotd.aggregate.save import get_aggregated_file_path, save_aggregated_data
from sotd.aggregate.user_aggregators import aggregate_user_blade_usage, aggregate_users


def process_month(year: int, month: int, args: argparse.Namespace) -> Dict[str, Any]:
    """Process a single month of enriched data."""
    # Validate input parameters
    if not isinstance(year, int) or year < 2000 or year > 2100:
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Invalid year: {year} (must be between 2000-2100)",
        }

    if not isinstance(month, int) or month < 1 or month > 12:
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Invalid month: {month} (must be between 1-12)",
        }

    # Get file paths
    base_dir = Path(args.out_dir)
    enriched_path = get_enriched_file_path(base_dir, year, month)
    aggregated_path = get_aggregated_file_path(base_dir, year, month)

    if not enriched_path.exists():
        if args.debug:
            print(f"[DEBUG] Skipping missing enriched file: {enriched_path}")
        return {
            "year": year,
            "month": month,
            "status": "skipped",
            "reason": "missing_enriched_file",
        }

    # Check if output file exists and force flag
    if aggregated_path.exists() and not args.force:
        if args.debug:
            print(f"[DEBUG] Skipping existing aggregated file: {aggregated_path}")
        return {
            "year": year,
            "month": month,
            "status": "skipped",
            "reason": "file_exists",
        }

    try:
        # Load enriched data with enhanced validation
        metadata, data = load_enriched_data(enriched_path, debug=args.debug)

        # Validate that we have data to process
        if not data:
            if args.debug:
                print(f"[DEBUG] No data to process for {year:04d}-{month:02d}")
            return {
                "year": year,
                "month": month,
                "status": "skipped",
                "reason": "no_data",
            }

        # Filter for matched records
        matched_records = filter_matched_records(data, debug=args.debug)

        # Calculate basic metrics
        basic_metrics = calculate_basic_metrics(matched_records, debug=args.debug)

        # Perform core aggregations
        results = _perform_core_aggregations(matched_records, args.debug)

        # Perform specialized aggregations if enabled
        specialized_results = _perform_specialized_aggregations(matched_records, args)

        # Perform cross-product analysis if enabled
        cross_product_results = _perform_cross_product_analysis(matched_records, args)

        # Combine all results
        all_aggregations = {**results, **specialized_results, **cross_product_results}

        # Prepare final results
        final_results = _prepare_final_results(
            year, month, basic_metrics, all_aggregations, data, matched_records
        )

        # Save aggregated data
        save_aggregated_data(final_results, aggregated_path, force=args.force, debug=args.debug)

        if args.debug:
            print(f"[DEBUG] Processed {year:04d}-{month:02d}: {final_results['summary']}")

        return final_results

    except FileNotFoundError as e:
        if args.debug:
            print(f"[DEBUG] File not found error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"File not found: {e}",
        }
    except json.JSONDecodeError as e:
        if args.debug:
            print(f"[DEBUG] JSON decode error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"JSON decode error: {e}",
        }
    except ValueError as e:
        if args.debug:
            print(f"[DEBUG] Data validation error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Data validation error: {e}",
        }
    except OSError as e:
        if args.debug:
            print(f"[DEBUG] File system error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"File system error: {e}",
        }
    except Exception as e:
        if args.debug:
            print(f"[DEBUG] Unexpected error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Unexpected error: {e}",
        }


def _perform_core_aggregations(
    matched_records: List[Dict[str, Any]], debug: bool
) -> Dict[str, Any]:
    """Perform core product and user aggregations."""
    return {
        "razors": aggregate_razors(matched_records, debug=debug),
        "razor_manufacturers": aggregate_razor_manufacturers(matched_records, debug=debug),
        "blades": aggregate_blades(matched_records, debug=debug),
        "blade_manufacturers": aggregate_blade_manufacturers(matched_records, debug=debug),
        "soaps": aggregate_soaps(matched_records, debug=debug),
        "soap_makers": aggregate_soap_makers(matched_records, debug=debug),
        "brushes": aggregate_brushes(matched_records, debug=debug),
        "brush_knot_makers": aggregate_brush_knot_makers(matched_records, debug=debug),
        "brush_handle_makers": aggregate_brush_handle_makers(matched_records, debug=debug),
        "brush_fibers": aggregate_brush_fibers(matched_records, debug=debug),
        "brush_knot_sizes": aggregate_brush_knot_sizes(matched_records, debug=debug),
        "users": aggregate_users(matched_records, debug=debug),
    }


def _perform_specialized_aggregations(
    matched_records: List[Dict[str, Any]], args: argparse.Namespace
) -> Dict[str, Any]:
    """Perform specialized aggregations if enabled."""
    # Determine which specialized aggregations to run based on CLI flags
    run_specialized = getattr(args, "enable_specialized", False) or not getattr(
        args, "disable_specialized", False
    )

    if args.debug:
        print("[DEBUG] Aggregation settings:")
        print(f"  Specialized aggregations: {'enabled' if run_specialized else 'disabled'}")

    if not run_specialized:
        return {
            "blackbird_plates": [],
            "christopher_bradley_plates": [],
            "game_changer_plates": [],
            "super_speed_tips": [],
            "straight_razor_specs": [],
        }

    if args.debug:
        print("[DEBUG] Running specialized aggregations...")

    return {
        "blackbird_plates": aggregate_blackbird_plates(matched_records, debug=args.debug),
        "christopher_bradley_plates": aggregate_christopher_bradley_plates(
            matched_records, debug=args.debug
        ),
        "game_changer_plates": aggregate_game_changer_plates(matched_records, debug=args.debug),
        "super_speed_tips": aggregate_super_speed_tips(matched_records, debug=args.debug),
        "straight_razor_specs": aggregate_straight_razor_specs(matched_records, debug=args.debug),
    }


def _perform_cross_product_analysis(
    matched_records: List[Dict[str, Any]], args: argparse.Namespace
) -> Dict[str, Any]:
    """Perform cross-product analysis if enabled."""
    # Determine which cross-product analysis to run based on CLI flags
    run_cross_product = getattr(args, "enable_cross_product", False) or not getattr(
        args, "disable_cross_product", False
    )

    if args.debug:
        print(f"  Cross-product analysis: {'enabled' if run_cross_product else 'disabled'}")

    if not run_cross_product:
        return {
            "razor_blade_combinations": [],
            "user_blade_usage": [],
        }

    if args.debug:
        print("[DEBUG] Running cross-product analysis...")

    return {
        "razor_blade_combinations": aggregate_razor_blade_combinations(
            matched_records, debug=args.debug
        ),
        "user_blade_usage": aggregate_user_blade_usage(matched_records, debug=args.debug),
    }


def _prepare_final_results(
    year: int,
    month: int,
    basic_metrics: Dict[str, Any],
    aggregations: Dict[str, Any],
    data: List[Dict[str, Any]],
    matched_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Prepare the final results structure."""
    return {
        "year": year,
        "month": month,
        "status": "success",
        "basic_metrics": basic_metrics,
        "aggregations": aggregations,
        "summary": {
            "total_records": len(data),
            "matched_records": len(matched_records),
            "razor_count": len(aggregations["razors"]),
            "razor_manufacturer_count": len(aggregations["razor_manufacturers"]),
            "blade_count": len(aggregations["blades"]),
            "blade_manufacturer_count": len(aggregations["blade_manufacturers"]),
            "soap_count": len(aggregations["soaps"]),
            "soap_maker_count": len(aggregations["soap_makers"]),
            "brush_count": len(aggregations["brushes"]),
            "brush_knot_maker_count": len(aggregations["brush_knot_makers"]),
            "brush_handle_maker_count": len(aggregations["brush_handle_makers"]),
            "brush_fiber_count": len(aggregations["brush_fibers"]),
            "brush_knot_size_count": len(aggregations["brush_knot_sizes"]),
            "user_count": len(aggregations["users"]),
            "blackbird_plate_count": len(aggregations["blackbird_plates"]),
            "christopher_bradley_plate_count": len(aggregations["christopher_bradley_plates"]),
            "game_changer_plate_count": len(aggregations["game_changer_plates"]),
            "super_speed_tip_count": len(aggregations["super_speed_tips"]),
            "straight_razor_spec_count": len(aggregations["straight_razor_specs"]),
            "razor_blade_combination_count": len(aggregations["razor_blade_combinations"]),
            "user_blade_usage_count": len(aggregations["user_blade_usage"]),
        },
    }
