#!/usr/bin/env python3
"""
Script to demonstrate A/B comparison between legacy and scoring brush systems.

This script loads data from both systems and performs a comprehensive comparison
to analyze differences in matching results, performance, and accuracy.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sotd.match.brush_parallel_data_manager import BrushParallelDataManager
from sotd.match.brush_system_comparator import BrushSystemComparator


def load_system_data(month: str) -> tuple[dict, dict]:
    """Load data from both brush systems for comparison."""
    manager = BrushParallelDataManager(base_path=Path("data"))

    # Load data from both systems
    old_data = manager.load_data(month, "current")
    new_data = manager.load_data(month, "new")

    return old_data, new_data


def main():
    """Main comparison function."""
    month = "2025-05"

    print(f"🔍 Comparing brush systems for {month}")
    print("=" * 60)

    try:
        # Load data from both systems
        print("📂 Loading data from both systems...")
        old_data, new_data = load_system_data(month)

        print(f"✅ Legacy system: {len(old_data.get('data', []))} records")
        print(f"✅ Scoring system: {len(new_data.get('data', []))} records")

        # Create comparator
        print("\n🔬 Creating comparison framework...")
        comparator = BrushSystemComparator(old_data, new_data)

        # Perform comparison
        print("📊 Running comparison analysis...")
        comparator.compare_matches()

        # Generate report
        print("📋 Generating comprehensive report...")
        report = comparator.generate_report()

        # Display key findings
        print("\n📈 COMPARISON RESULTS")
        print("=" * 60)

        summary = report["summary"]
        print(f"Total Records: {summary['total_records']}")

        # Calculate agreement rate (matching results + both unmatched)
        agreement_rate = (
            summary["matching_results"]["percentage"] + summary["both_unmatched"]["percentage"]
        )
        disagreement_rate = summary["different_results"]["percentage"]

        print(f"Agreement Rate: {agreement_rate:.1f}%")
        print(f"Disagreement Rate: {disagreement_rate:.1f}%")

        # Calculate success rates
        old_success_rate = (
            summary["matching_results"]["percentage"] + summary["old_only_matches"]["percentage"]
        )
        new_success_rate = (
            summary["matching_results"]["percentage"] + summary["new_only_matches"]["percentage"]
        )

        print(f"Legacy System Success: {old_success_rate:.1f}%")
        print(f"Scoring System Success: {new_success_rate:.1f}%")

        # Show detailed breakdown
        print("\n📊 DETAILED BREAKDOWN")
        print("-" * 40)
        for category, data in summary.items():
            if isinstance(data, dict) and "count" in data and "percentage" in data:
                print(
                    f"{category.replace('_', ' ').title()}: {data['count']} ({data['percentage']:.1f}%)"
                )

        # Show match type changes
        if report["match_type_changes"]:
            print("\n🔄 MATCH TYPE CHANGES")
            print("-" * 40)
            for change_type, count in report["match_type_changes"].items():
                print(f"{change_type}: {count}")

        # Show performance comparison
        print("\n⚡ PERFORMANCE COMPARISON")
        print("-" * 40)
        performance = comparator.get_performance_comparison()

        old_perf = performance["old_system_performance"]
        new_perf = performance["new_system_performance"]

        if old_perf and new_perf:
            old_processing_time = old_perf.get("processing_time_seconds", 0)
            new_processing_time = new_perf.get("processing_time_seconds", 0)

            print(f"Legacy System Processing Time: {old_processing_time:.2f}s")
            print(f"Scoring System Processing Time: {new_processing_time:.2f}s")

            if old_processing_time > 0 and new_processing_time > 0:
                if new_processing_time > old_processing_time:
                    slowdown = new_processing_time / old_processing_time
                    print(f"Scoring System is {slowdown:.1f}x slower than Legacy System")
                else:
                    speedup = old_processing_time / new_processing_time
                    print(f"Scoring System is {speedup:.1f}x faster than Legacy System")

            # Show file I/O times
            old_io_time = old_perf.get("file_io_time_seconds", 0)
            new_io_time = new_perf.get("file_io_time_seconds", 0)
            if old_io_time > 0 or new_io_time > 0:
                print(f"Legacy System I/O Time: {old_io_time:.3f}s")
                print(f"Scoring System I/O Time: {new_io_time:.3f}s")

        # Show sample differences with strategy information
        if report["detailed_differences"]:
            print("\n🔍 SAMPLE DIFFERENCES (showing first 3)")
            print("-" * 40)
            for i, diff in enumerate(report["detailed_differences"][:3]):
                print(f"\nDifference #{i + 1}:")
                print(f"  Record Index: {diff['record_index']}")
                print(f"  Original: {diff['input_text']}")
                print(
                    f"  Legacy: {diff['old_match']['brand']} {diff['old_match']['model']} "
                    f"({diff['old_match']['match_type']} - {diff['old_match']['strategy']})"
                )
                print(
                    f"  Scoring: {diff['new_match']['brand']} {diff['new_match']['model']} "
                    f"({diff['new_match']['match_type']} - {diff['new_match']['strategy']})"
                )

                # Show strategy selection analysis
                old_strategy = diff["old_match"]["strategy"]
                new_strategy = diff["new_match"]["strategy"]
                if old_strategy != new_strategy:
                    print(f"  Strategy Change: {old_strategy} → {new_strategy}")

                    # Show composite brush details if available
                    if new_strategy == "dual_component":
                        print("  Composite Brush: Handle + Knot components")
                        # Could add more detailed breakdown here if needed

        # Save detailed report
        output_path = Path("data") / f"brush_system_comparison_{month}.json"
        comparator.save_comparison_report(output_path)
        print(f"\n💾 Detailed report saved to: {output_path}")

        # Statistical summary
        print("\n📊 STATISTICAL SUMMARY")
        print("-" * 40)
        stats = comparator.get_statistical_summary()

        print(f"Most Common Change: {stats['most_common_match_type_change']}")
        print(f"Brand Changes: {stats['difference_categories']['brand_changes']}")
        print(f"Model Changes: {stats['difference_categories']['model_changes']}")
        print(f"Fiber Changes: {stats['difference_categories']['fiber_changes']}")

        print("\n✅ Comparison complete!")

    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
