#!/usr/bin/env python3
"""Comprehensive test of the new universal table generator with real data."""

import json
from pathlib import Path

from sotd.report.table_generators.table_generator import TableGenerator


def test_with_real_data():
    """Test the new TableGenerator with real aggregated data."""

    # Load real aggregated data
    data_file = Path("data/aggregated/2025-08.json")
    if not data_file.exists():
        print(f"Data file not found: {data_file}")
        return

    print("Loading real aggregated data...")
    with open(data_file, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    # Extract the data section
    if "data" in full_data:
        data = full_data["data"]
        metadata = full_data.get("meta", {})
    else:
        data = full_data
        metadata = {}

    print(f"Loaded data with keys: {list(data.keys())}")
    print(f"Metadata keys: {list(metadata.keys())}")

    # Initialize the new table generator
    table_generator = TableGenerator(full_data)

    print(f"\nAvailable table names: {table_generator.get_available_table_names()}")

    # Test with razors data
    if "razors" in data:
        print("\n=== Testing Razors Table Generation ===")

        # Basic table generation
        razors_table = table_generator.generate_table("razors")
        print("Basic razors table (first 3 lines):")
        lines = razors_table.split("\n")
        for i, line in enumerate(lines[:3]):
            print(f"  {i + 1}: {line}")

        # Test ranks filtering
        razors_top5 = table_generator.generate_table("razors", ranks=5)
        print("Razors table (top 5 ranks):")
        lines = razors_top5.split("\n")
        for i, line in enumerate(lines[:3]):
            print(f"  {i + 1}: {line}")

        # Test rows limiting
        razors_first3 = table_generator.generate_table("razors", rows=3)
        print("Razors table (first 3 rows):")
        lines = razors_first3.split("\n")
        for i, line in enumerate(lines[:3]):
            print(f"  {i + 1}: {line}")

        # Test both parameters
        razors_limited = table_generator.generate_table("razors", ranks=3, rows=2)
        print("Razors table (rank 3, max 2 rows):")
        lines = razors_limited.split("\n")
        for i, line in enumerate(lines[:3]):
            print(f"  {i + 1}: {line}")

    # Test with soap makers data
    if "soap_makers" in data:
        print("\n=== Testing Soap Makers Table Generation ===")

        soap_table = table_generator.generate_table("soap-makers")
        print("Soap makers table (first 3 lines):")
        lines = soap_table.split("\n")
        for i, line in enumerate(lines[:3]):
            print(f"  {i + 1}: {line}")

        # Test parameter filtering
        soap_top10 = table_generator.generate_table("soap-makers", ranks=10)
        print("Soap makers table (top 10 ranks):")
        lines = soap_top10.split("\n")
        for i, line in enumerate(lines[:3]):
            print(f"  {i + 1}: {line}")

    # Test error handling
    print("\n=== Testing Error Handling ===")

    try:
        table_generator.generate_table("unknown-table")
    except ValueError as e:
        print(f"✅ Correctly caught unknown table error: {e}")

    try:
        table_generator.generate_table("razors", ranks=0)
    except ValueError as e:
        print(f"✅ Correctly caught invalid ranks error: {e}")

    try:
        table_generator.generate_table("razors", rows=-1)
    except ValueError as e:
        print(f"✅ Correctly caught invalid rows error: {e}")

    print("\n=== Performance Testing ===")

    # Test performance with larger datasets
    if "razors" in data:
        import time

        start_time = time.time()
        for _ in range(100):
            table_generator.generate_table("razors", ranks=50)
        end_time = time.time()

        print(f"Generated 100 tables with ranks=50 in {end_time - start_time:.3f} seconds")
        print(f"Average time per table: {(end_time - start_time) / 100:.3f} seconds")

    print("\n🎉 Real data integration test completed successfully!")


if __name__ == "__main__":
    test_with_real_data()
