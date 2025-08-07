#!/usr/bin/env python3
"""Simple test script to debug comparison issue."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sotd.match.brush_system_comparator import BrushSystemComparator
from sotd.match.brush_parallel_data_manager import BrushParallelDataManager


def main():
    """Test the comparison functionality."""
    month = "2025-05"

    print(f"Testing comparison for {month}")

    # Load data
    manager = BrushParallelDataManager(base_path=Path("data"))
    old_data = manager.load_data(month, "current")
    new_data = manager.load_data(month, "new")

    print(f"Old data type: {type(old_data)}")
    print(f"New data type: {type(new_data)}")

    if old_data is None or new_data is None:
        print("❌ Data loading failed")
        return 1

    print(f"Old data keys: {list(old_data.keys())}")
    print(f"New data keys: {list(new_data.keys())}")

    # Test comparator creation
    try:
        comparator = BrushSystemComparator(old_data, new_data)
        print("✅ Comparator created successfully")

        # Test comparison
        results = comparator.compare_matches()
        print("✅ Comparison completed successfully")
        print(f"Results keys: {list(results.keys())}")

        # Test report generation
        report = comparator.generate_report()
        print("✅ Report generated successfully")
        print(f"Report keys: {list(report.keys())}")

        # Show summary
        stats = comparator.get_statistical_summary()
        print(f"\n📊 SUMMARY:")
        print(f"Total Records: {stats['total_records']}")
        print(f"Agreement Rate: {stats['agreement_rate']:.1f}%")
        print(f"Disagreement Rate: {stats['disagreement_rate']:.1f}%")
        print(f"Legacy System Success: {stats['old_system_success_rate']:.1f}%")
        print(f"Scoring System Success: {stats['new_system_success_rate']:.1f}%")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
