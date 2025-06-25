#!/usr/bin/env python3
"""Script to alphabetize entries in correct_matches.yaml."""

from pathlib import Path

import yaml


def alphabetize_correct_matches(file_path: Path) -> None:
    """Alphabetize entries in correct_matches.yaml while preserving structure."""

    # Load the current file
    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        print("No data found in correct_matches.yaml")
        return

    # Alphabetize entries within each field/brand/model
    for field, field_data in data.items():
        if isinstance(field_data, dict):
            for brand, brand_data in field_data.items():
                if isinstance(brand_data, dict):
                    for model, entries in brand_data.items():
                        if isinstance(entries, list):
                            # Sort entries alphabetically (case-insensitive)
                            entries.sort(key=str.lower)

    # Create backup
    backup_path = file_path.with_suffix(".yaml.backup")
    import shutil

    shutil.copy2(file_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Write alphabetized data back
    with file_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, indent=2, allow_unicode=True)

    print(f"Alphabetized entries in {file_path}")


def main():
    """Main entry point."""
    file_path = Path("data/correct_matches.yaml")

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    print(f"Alphabetizing entries in {file_path}...")
    alphabetize_correct_matches(file_path)
    print("Done!")


if __name__ == "__main__":
    main()
