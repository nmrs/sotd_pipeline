#!/usr/bin/env python3
"""Test script for filtered entries manager."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from sotd.utils.filtered_entries import FilteredEntriesManager  # noqa: E402


def test_add_entry():
    """Test the add_entry method with reason."""
    # Create a temporary file
    test_file = Path("test_filtered_entries.yaml")

    # Create manager
    manager = FilteredEntriesManager(test_file)

    # Test adding an entry with reason
    manager.add_entry(
        category="blade",
        entry_name="AC Blade",
        comment_id="mvtucxo",
        file_path="2025-06.json",
        source="user",
        reason="not specific enough for matching",
    )

    # Save and check the result
    manager.save()

    # Read the file to see the structure
    with open(test_file, "r") as f:
        content = f.read()
        print("Generated YAML:")
        print(content)

    # Clean up
    test_file.unlink()


if __name__ == "__main__":
    test_add_entry()
