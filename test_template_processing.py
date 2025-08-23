#!/usr/bin/env python3
"""Test template processing with the new universal table generator."""

import json
from pathlib import Path

from sotd.report.monthly_generator import MonthlyReportGenerator


def test_template_processing():
    """Test that the monthly generator can process templates with the new table generator."""

    # Load real aggregated data
    data_file = Path("data/aggregated/2025-08.json")
    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        return

    print("Loading real aggregated data...")
    with open(data_file, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    # Extract metadata and data
    metadata = full_data.get("meta", {})
    data = full_data.get("data", full_data)

    print(f"Loaded data with {len(data)} aggregators")
    print(f"Metadata: month={metadata.get('month', 'Unknown')}")

    # Create monthly generator with test template
    monthly_gen = MonthlyReportGenerator("hardware", metadata, data, template_path="test_templates")

    print("\nTesting template processing...")

    try:
        # Generate the report content
        result = monthly_gen.generate_notes_and_caveats()

        print("✅ Template processing successful!")
        print(f"Generated content length: {len(result)} characters")

        # Show first few lines
        print("\nFirst 10 lines of generated content:")
        lines = result.split("\n")
        for i, line in enumerate(lines[:10]):
            print(f"  {i + 1:2d}: {line}")

        # Check if tables were generated
        if "|   rank |   shaves |   unique_users | name" in result:
            print("\n✅ Razors table generated correctly")
        else:
            print("\n❌ Razors table not found in output")

        if "|   rank |   shaves |   unique_users | maker" in result:
            print("✅ Soap makers table generated correctly")
        else:
            print("❌ Soap makers table not found in output")

        # Check for parameter filtering
        if "Top 5 Razors" in result and "|      5 |" in result:
            print("✅ Parameter filtering (ranks:5) working correctly")
        else:
            print("❌ Parameter filtering not working")

    except Exception as e:
        print(f"❌ Template processing failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n🎉 Template processing test completed!")


if __name__ == "__main__":
    test_template_processing()
