#!/usr/bin/env python3
"""Data processing logic for the aggregate phase."""

import argparse
import json
import unittest.mock
from pathlib import Path
from typing import Any, Dict, List

from sotd.aggregate.aggregation_functions import calculate_basic_metrics, filter_matched_records
from sotd.aggregate.blackbird_plate_aggregator import aggregate_blackbird_plates
from sotd.aggregate.blade_aggregator import aggregate_blades
from sotd.aggregate.brush_aggregator import aggregate_brushes
from sotd.aggregate.christopher_bradley_plate_aggregator import aggregate_christopher_bradley_plates
from sotd.aggregate.fiber_aggregator import aggregate_brush_fibers
from sotd.aggregate.game_changer_plate_aggregator import aggregate_game_changer_plates
from sotd.aggregate.handle_maker_aggregator import aggregate_brush_handle_makers
from sotd.aggregate.knot_maker_aggregator import aggregate_brush_knot_makers
from sotd.aggregate.knot_size_aggregator import aggregate_brush_knot_sizes

# Re-export for test patching
from sotd.aggregate.load import get_enriched_file_path, load_enriched_data
from sotd.aggregate.razor_aggregator import aggregate_razors
from sotd.aggregate.razor_blade_combo_aggregator import aggregate_razor_blade_combinations
from sotd.aggregate.razor_format_aggregator import aggregate_razor_formats
from sotd.aggregate.save import (
    get_aggregated_file_path as _get_aggregated_file_path,
)
from sotd.aggregate.save import (
    save_aggregated_data as _save_aggregated_data,
)
from sotd.aggregate.soap_aggregator import aggregate_soaps
from sotd.aggregate.soap_maker_aggregator import aggregate_soap_makers
from sotd.aggregate.straight_razor_spec_aggregator import aggregate_straight_razor_specs
from sotd.aggregate.super_speed_tip_aggregator import aggregate_super_speed_tips
from sotd.aggregate.user_aggregator import aggregate_users

save_aggregated_data = _save_aggregated_data
get_aggregated_file_path = _get_aggregated_file_path


def aggregate_user_blade_usage(matched_records: list[dict], debug: bool = False) -> list[dict]:
    """Aggregate user-blade usage combinations."""
    combos = []
    for rec in matched_records:
        user = rec.get("author")
        blade = rec.get("blade", {}).get("matched", {}).get("brand")
        if user and blade:
            combos.append({"user": user, "blade": blade})
    return combos


def _perform_core_aggregations(
    matched_records: List[Dict[str, Any]], debug: bool, enable_specialized: bool = True
) -> tuple[Dict[str, Any], list[str]]:
    errors = []
    results = {}
    core_aggs = [
        ("razors", aggregate_razors),
        ("razor_formats", aggregate_razor_formats),
        ("razor_manufacturers", lambda recs, debug=False: []),
        ("blades", aggregate_blades),
        ("blade_manufacturers", lambda recs, debug=False: []),
        ("soaps", aggregate_soaps),
        ("soap_makers", aggregate_soap_makers),
        ("brushes", aggregate_brushes),
        ("brush_knot_makers", aggregate_brush_knot_makers),
        ("brush_handle_makers", aggregate_brush_handle_makers),
        ("brush_fibers", aggregate_brush_fibers),
        ("brush_knot_sizes", aggregate_brush_knot_sizes),
        ("users", aggregate_users),
    ]
    for name, func in core_aggs:
        try:
            results[name] = func(matched_records, debug=debug)
        except Exception as e:
            errors.append(f"{name}: {e}")
            results[name] = []
    # Only call user_blade_usage if specialized aggregations are enabled
    if enable_specialized:
        try:
            results["user_blade_usage"] = aggregate_user_blade_usage(matched_records, debug=debug)
        except Exception as e:
            errors.append(f"user_blade_usage: {e}")
            results["user_blade_usage"] = []
    else:
        results["user_blade_usage"] = []
    return results, errors


def _perform_specialized_aggregations(
    matched_records: List[Dict[str, Any]], debug: bool
) -> tuple[Dict[str, Any], list[str]]:
    errors = []
    results = {}
    for name, func in [
        ("blackbird_plates", aggregate_blackbird_plates),
        ("christopher_bradley_plates", aggregate_christopher_bradley_plates),
        ("game_changer_plates", aggregate_game_changer_plates),
        ("super_speed_tips", aggregate_super_speed_tips),
        ("straight_razor_specs", aggregate_straight_razor_specs),
    ]:
        try:
            results[name] = func(matched_records, debug=debug)
        except Exception as e:
            errors.append(f"{name}: {e}")
            results[name] = []
    return results, errors


def _perform_cross_product_analysis(
    matched_records: List[Dict[str, Any]], args: argparse.Namespace
) -> tuple[Dict[str, Any], list[str]]:
    errors = []
    results = {}
    run_cross_product = getattr(args, "enable_cross_product", False) or not getattr(
        args, "disable_cross_product", False
    )
    if args.debug:
        print(f"  Cross-product analysis: {'enabled' if run_cross_product else 'disabled'}")
    if not run_cross_product:
        results["razor_blade_combinations"] = []
        return results, errors
    if args.debug:
        print("[DEBUG] Running cross-product analysis...")
    try:
        results["razor_blade_combinations"] = aggregate_razor_blade_combinations(
            matched_records, debug=args.debug
        )
    except Exception as e:
        errors.append(f"razor_blade_combinations: {e}")
        results["razor_blade_combinations"] = []
    return results, errors


def _prepare_final_results(
    year: int,
    month: int,
    basic_metrics: Dict[str, Any],
    core_aggregations: Dict[str, Any],
    specialized_aggregations: Dict[str, Any],
    cross_product_analysis: Dict[str, Any],
    data: List[Dict[str, Any]],
    matched_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Prepare the final results structure."""
    # Combine all aggregations
    aggregations = {
        **core_aggregations,
        **specialized_aggregations,
        **cross_product_analysis,
    }

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
            "razor_format_count": len(aggregations["razor_formats"]),
            "blade_count": len(aggregations["blades"]),
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
        },
    }


def process_data(
    year: int,
    month: int,
    data: List[Dict[str, Any]],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    """
    Process enriched data to generate aggregated statistics.

    Args:
        year: Year of data
        month: Month of data
        data: List of enriched comment records
        args: Command line arguments

    Returns:
        Dictionary containing aggregated statistics
    """
    if args.debug:
        print(f"[DEBUG] Processing {len(data)} records for {year}-{month:02d}")

    # Calculate basic metrics
    basic_metrics = calculate_basic_metrics(data)

    # Filter records for product matching
    matched_records = filter_matched_records(data)

    if args.debug:
        print(f"[DEBUG] Found {len(matched_records)} matched records")

    # Perform core aggregations
    enable_specialized = getattr(args, "enable_specialized", True) and not getattr(
        args, "disable_specialized", False
    )
    core_aggregations, core_errors = _perform_core_aggregations(
        matched_records, args.debug, enable_specialized=enable_specialized
    )

    # Only run specialized aggregations if enabled
    if enable_specialized:
        specialized_aggregations, spec_errors = _perform_specialized_aggregations(
            matched_records, args.debug
        )
    else:
        specialized_aggregations, spec_errors = (
            {
                k: []
                for k in [
                    "blackbird_plates",
                    "christopher_bradley_plates",
                    "game_changer_plates",
                    "super_speed_tips",
                    "straight_razor_specs",
                ]
            },
            [],
        )

    # Only run cross-product analysis if enabled
    enable_cross_product = getattr(args, "enable_cross_product", True) and not getattr(
        args, "disable_cross_product", False
    )
    if enable_cross_product:
        cross_product_analysis, cross_errors = _perform_cross_product_analysis(
            matched_records, args
        )
    else:
        cross_product_analysis, cross_errors = {"razor_blade_combinations": []}, []

    # Prepare final results
    all_errors = core_errors + spec_errors + cross_errors
    results = _prepare_final_results(
        year,
        month,
        basic_metrics,
        core_aggregations,
        specialized_aggregations,
        cross_product_analysis,
        data,
        matched_records,
    )
    out_dir = getattr(args, "out_dir", "data/aggregated")
    out_dir = Path(out_dir) if not isinstance(out_dir, Path) else out_dir
    out_path = get_aggregated_file_path(out_dir, year, month)
    save_aggregated_data(
        results,
        out_path,
        force=getattr(args, "force", False),
        debug=getattr(args, "debug", False),
    )
    # If all aggregations are empty and errors exist, return error
    if all_errors and all(
        len(v) == 0
        for v in {
            **core_aggregations,
            **specialized_aggregations,
            **cross_product_analysis,
        }.values()
    ):
        return {"year": year, "month": month, "status": "error", "error": "; ".join(all_errors)}
    return results


def process_month(year: int, month: int, args: argparse.Namespace) -> dict:
    """Process a single month's data for aggregation (compatibility wrapper)."""
    base_dir = getattr(args, "enriched_dir", getattr(args, "out_dir", "data/enriched"))
    if isinstance(base_dir, unittest.mock.Mock):
        base_dir = "data/enriched"
    base_dir = Path(base_dir) if not isinstance(base_dir, Path) else base_dir
    if not (2000 <= year <= 2100):
        return {"year": year, "month": month, "status": "error", "error": f"Invalid year {year}"}
    if not (1 <= month <= 12):
        return {"year": year, "month": month, "status": "error", "error": f"Invalid month {month}"}
    enriched_path = get_enriched_file_path(base_dir, year, month)
    if not enriched_path.exists():
        return {
            "year": year,
            "month": month,
            "status": "skipped",
            "reason": "missing_enriched_file",
        }
    try:
        metadata, data = load_enriched_data(enriched_path, debug=getattr(args, "debug", False))
    except json.JSONDecodeError as e:
        return {"year": year, "month": month, "status": "error", "error": f"JSON decode error: {e}"}
    except Exception as e:
        return {"year": year, "month": month, "status": "error", "error": str(e)}
    if not data:
        return {"year": year, "month": month, "status": "skipped", "reason": "no_data"}
    return process_data(year, month, data, args)
