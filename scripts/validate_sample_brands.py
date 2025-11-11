#!/usr/bin/env python3
"""
Script to validate sample brands by analyzing enriched data files.
This will help verify that our sample_brands calculation is correct.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def analyze_sample_brands(month: str) -> dict:
    """Analyze sample brands for a specific month."""
    enriched_file = Path(f"data/enriched/{month}.json")

    if not enriched_file.exists():
        print(f"❌ Enriched file not found: {enriched_file}")
        return {}

    print(f"🔍 Analyzing sample brands for {month}...")

    with open(enriched_file, "r") as f:
        data = json.load(f)

    records = data.get("data", [])
    print(f"📊 Total records: {len(records):,}")

    # Track sample brands and their details
    sample_brands = defaultdict(list)
    total_samples = 0

    for i, record in enumerate(records):
        soap = record.get("soap")
        if not soap:
            continue

        enriched = soap.get("enriched", {})
        matched = soap.get("matched", {})

        # Check if this is a sample
        sample_type = enriched.get("sample_type")
        if sample_type:
            total_samples += 1
            brand = matched.get("brand")
            if brand:
                sample_brands[brand].append(
                    {
                        "record_index": i,
                        "sample_type": sample_type,
                        "author": record.get("author", "Unknown"),
                        "brand": brand,
                        "scent": matched.get("scent", "Unknown"),
                    }
                )

    print(f"📈 Total samples found: {total_samples}")
    print(f"🏷️  Unique sample brands: {len(sample_brands)}")

    # Show details for each sample brand
    print("\n📋 Sample Brand Details:")
    for brand, samples in sample_brands.items():
        print(f"\n  **{brand}** ({len(samples)} samples):")
        for sample in samples:
            print(
                f"    - Record {sample['record_index']}: {sample['sample_type']} by "
                f"{sample['author']} ({sample['scent']})"
            )

    return {
        "month": month,
        "total_records": len(records),
        "total_samples": total_samples,
        "unique_sample_brands": len(sample_brands),
        "sample_brands": dict(sample_brands),
    }


def validate_sample_brands_calculation(month: str) -> bool:
    """Validate that our sample_brands calculation matches the actual data."""
    print(f"\n🔍 Validating sample_brands calculation for {month}...")

    # Import the metrics function
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from sotd.aggregate.utils.metrics import calculate_sample_brands

    # Load the enriched data
    enriched_file = Path(f"data/enriched/{month}.json")
    with open(enriched_file, "r") as f:
        data = json.load(f)

    records = data.get("data", [])

    # Calculate using our function
    calculated_count = calculate_sample_brands(records)

    # Count manually for validation
    manual_count = 0
    for record in records:
        soap = record.get("soap")
        if soap:
            enriched = soap.get("enriched", {})
            if enriched.get("sample_type"):
                manual_count += 1

    print(f"📊 Manual count of records with sample_type: {manual_count}")
    print(f"📊 Our function result: {calculated_count}")

    if calculated_count == manual_count:
        print("✅ Sample brands calculation is CORRECT")
        return True
    else:
        print("❌ Sample brands calculation is INCORRECT")
        return False


def main():
    """Main analysis function."""
    print("🔍 Sample Brands Validation Script")
    print("=" * 50)

    months = ["2025-06", "2025-07"]

    all_results = {}
    validation_passed = True

    for month in months:
        print(f"\n{'=' * 20} {month} {'=' * 20}")

        # Analyze the data
        result = analyze_sample_brands(month)
        if result:
            all_results[month] = result

        # Validate our calculation
        if not validate_sample_brands_calculation(month):
            validation_passed = False

    # Summary
    print(f"\n{'=' * 50}")
    print("📊 SUMMARY")
    print("=" * 50)

    for month, result in all_results.items():
        print(f"\n{month}:")
        print(f"  - Total records: {result['total_records']:,}")
        print(f"  - Total samples: {result['total_samples']:,}")
        print(f"  - Unique sample brands: {result['unique_sample_brands']:,}")

    if validation_passed:
        print("\n✅ All validations passed - sample_brands calculation is correct")
    else:
        print("\n❌ Validation failed - sample_brands calculation has issues")

    return validation_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
