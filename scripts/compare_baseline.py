#!/usr/bin/env python3
"""
Updated baseline comparison script for pandas optimization validation.
Compares current pipeline output against baseline files.
NO metadata fields are ignored - all content must be identical.
"""

import json
import sys
from pathlib import Path


def compare_json_files(baseline_path, current_path, description):
    """Compare JSON files - all content must be identical."""
    try:
        with open(baseline_path, "r") as f:
            baseline = json.load(f)
        with open(current_path, "r") as f:
            current = json.load(f)

        # Compare entire files - no metadata to ignore
        if baseline == current:
            print(f"✅ {description}: Identical")
            return True
        else:
            print(f"❌ {description}: Data content differs - STOP IMMEDIATELY")
            return False

    except Exception as e:
        print(f"❌ Error comparing {description}: {e}")
        return False


def compare_md_files(baseline_path, current_path, description):
    """Compare Markdown files - all content must be identical."""
    try:
        with open(baseline_path, "r") as f:
            baseline = f.read()
        with open(current_path, "r") as f:
            current = f.read()

        # Compare entire content - no timestamps to ignore
        if baseline == current:
            print(f"✅ {description}: Identical")
            return True
        else:
            print(f"❌ {description}: Content differs - STOP IMMEDIATELY")
            return False

    except Exception as e:
        print(f"❌ Error comparing {description}: {e}")
        return False


def main():
    """Main comparison function."""
    baseline_dir = Path(".ab_backups/baseline_pandas_optimization")

    if not baseline_dir.exists():
        print("❌ Baseline directory not found. Run Step 0 first.")
        sys.exit(1)

    print("🔍 Comparing current output against baseline...")
    print("⚠️  IMPORTANT: All content must be identical - no metadata ignored")
    print("=" * 60)

    all_passed = True

    # Compare aggregated data
    for month in ["2025-06", "2025-07"]:
        baseline_file = baseline_dir / "aggregated" / f"{month}.json"
        current_file = Path(f"data/aggregated/{month}.json")

        if current_file.exists():
            if not compare_json_files(baseline_file, current_file, f"Aggregated {month}"):
                all_passed = False
        else:
            print(f"⚠️  Current file not found: {current_file}")

    # Compare reports
    for month in ["2025-06", "2025-07"]:
        for report_type in ["hardware", "software"]:
            baseline_file = baseline_dir / "report" / f"{month}-{report_type}.md"
            current_file = Path(f"data/report/{month}-{report_type}.md")

            if current_file.exists():
                if not compare_md_files(
                    baseline_file, current_file, f"Report {month}-{report_type}"
                ):
                    all_passed = False
            else:
                print(f"⚠️  Current file not found: {current_file}")

    print("=" * 60)
    if all_passed:
        print("🎉 All comparisons passed! Proceed with optimizations.")
    else:
        print("🚨 STOP IMMEDIATELY - Consult user for direction!")
        sys.exit(1)


if __name__ == "__main__":
    main()
