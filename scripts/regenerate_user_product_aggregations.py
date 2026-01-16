#!/usr/bin/env python3
"""Regenerate user analysis and product usage aggregations for all existing months.

This script processes all months that have enriched data and generates
the specialized aggregations (user_analysis and product_usage) for API performance.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sotd.aggregate.engine import process_single_month
from sotd.aggregate.load import load_enriched_data
from sotd.aggregate.processor import aggregate_all
from sotd.aggregate.save import save_product_usage_data, save_user_analysis_data


def find_available_months(data_dir: Path) -> list[str]:
    """Find all months with enriched data."""
    enriched_dir = data_dir / "enriched"
    if not enriched_dir.exists():
        return []

    months = []
    for file_path in enriched_dir.glob("*.json"):
        month = file_path.stem
        if month and len(month) == 7 and month[4] == "-":  # YYYY-MM format
            months.append(month)

    return sorted(months)


def regenerate_aggregations_for_month(month: str, data_dir: Path, force: bool = False) -> bool:
    """Regenerate user analysis and product usage aggregations for a single month."""
    try:
        # Check if aggregations already exist
        user_analysis_file = data_dir / "aggregated" / "user_analysis" / f"{month}.json"
        product_usage_file = data_dir / "aggregated" / "product_usage" / f"{month}.json"

        if not force and user_analysis_file.exists() and product_usage_file.exists():
            print(f"  {month}: aggregations already exist, skipping (use --force to regenerate)")
            return True

        # Load enriched data
        records = load_enriched_data(month, data_dir)

        if not records:
            print(f"  {month}: no records found")
            return False

        # Generate aggregations
        aggregated_data = aggregate_all(records, month, debug=False)

        # Extract specialized aggregations
        user_analysis = aggregated_data.pop("_user_analysis", {})
        product_usage = aggregated_data.pop("_product_usage", {})

        # Save specialized aggregations
        if user_analysis:
            save_user_analysis_data(user_analysis, month, data_dir)
            print(f"  {month}: saved user analysis ({len(user_analysis)} users)")

        if product_usage:
            save_product_usage_data(product_usage, month, data_dir)
            total_products = sum(len(products) for products in product_usage.values())
            print(f"  {month}: saved product usage ({total_products} products)")

        return True

    except Exception as e:
        print(f"  {month}: ERROR - {e}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Regenerate user analysis and product usage aggregations"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory (default: data)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if files exist",
    )
    parser.add_argument(
        "--months",
        nargs="+",
        help="Specific months to regenerate (YYYY-MM format). If not provided, all months are processed.",
    )

    args = parser.parse_args()

    data_dir = args.data_dir

    if args.months:
        months = args.months
    else:
        months = find_available_months(data_dir)

    if not months:
        print("No months found with enriched data")
        return 1

    print(f"Regenerating aggregations for {len(months)} month(s)...")
    print(f"Data directory: {data_dir}")
    if args.force:
        print("Force mode: regenerating all aggregations")

    success_count = 0
    error_count = 0

    for month in months:
        if regenerate_aggregations_for_month(month, data_dir, force=args.force):
            success_count += 1
        else:
            error_count += 1

    print(f"\nCompleted: {success_count} successful, {error_count} errors")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
