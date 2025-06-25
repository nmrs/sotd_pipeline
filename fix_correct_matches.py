#!/usr/bin/env python3
"""Clean up correct_matches.yaml by alphabetizing, stripping tags, and removing duplicates."""

import re
from pathlib import Path
from typing import Dict, List

import yaml


def load_competition_tags(tags_path: Path) -> Dict[str, List[str]]:
    """Load competition tags configuration."""
    if not tags_path.exists():
        return {"strip_tags": [], "preserve_tags": []}

    try:
        with tags_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {
            "strip_tags": data.get("strip_tags", []),
            "preserve_tags": data.get("preserve_tags", []),
        }
    except Exception:
        return {"strip_tags": [], "preserve_tags": []}


def strip_competition_tags(value: str, competition_tags: Dict[str, List[str]]) -> str:
    """
    Strip competition tags from a string while preserving useful ones.

    Args:
        value: Input string that may contain competition tags
        competition_tags: Configuration of tags to strip/preserve

    Returns:
        String with unwanted competition tags removed
    """
    if not isinstance(value, str):
        return value

    # Get tags to strip and preserve
    strip_tags = competition_tags.get("strip_tags", [])
    preserve_tags = competition_tags.get("preserve_tags", [])

    if not strip_tags:
        return value

    # Create a list of tags to actually strip (exclude preserve_tags)
    tags_to_strip = [tag for tag in strip_tags if tag not in preserve_tags]

    if not tags_to_strip:
        return value

    # Build regex pattern to match tags with word boundaries
    # This ensures we match whole tags, not partial matches
    # Also handle tags that might be wrapped in backticks or asterisks
    strip_pattern = r"[`*]*\$(" + "|".join(re.escape(tag) for tag in tags_to_strip) + r")\b[`*]*"

    # Remove the tags and clean up extra whitespace
    cleaned = re.sub(strip_pattern, "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
    cleaned = cleaned.strip()

    return cleaned


def clean_and_alphabetize_correct_matches(
    file_path: Path, competition_tags: Dict[str, List[str]]
) -> None:
    """Clean up correct_matches.yaml by alphabetizing, stripping tags, and removing duplicates."""

    # Load the current file
    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        print("No data found in correct_matches.yaml")
        return

    total_entries_before = 0
    total_entries_after = 0
    duplicates_removed = 0

    # Process entries within each field/brand/model
    for field, field_data in data.items():
        if isinstance(field_data, dict):
            for brand, brand_data in field_data.items():
                if isinstance(brand_data, dict):
                    for model, entries in brand_data.items():
                        if isinstance(entries, list):
                            total_entries_before += len(entries)

                            # Clean each entry by stripping tags
                            cleaned_entries = []
                            for entry in entries:
                                cleaned_entry = strip_competition_tags(entry, competition_tags)
                                if cleaned_entry and cleaned_entry not in cleaned_entries:
                                    cleaned_entries.append(cleaned_entry)

                            # Sort entries alphabetically (case-insensitive)
                            cleaned_entries.sort(key=str.lower)

                            # Update the entries
                            brand_data[model] = cleaned_entries
                            total_entries_after += len(cleaned_entries)
                            duplicates_removed += len(entries) - len(cleaned_entries)

    # Create backup
    backup_path = file_path.with_suffix(".yaml.backup")
    import shutil

    shutil.copy2(file_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Write cleaned and alphabetized data back
    with file_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, indent=2, allow_unicode=True)

    print(f"Cleaned and alphabetized entries in {file_path}")
    print(f"Total entries before: {total_entries_before}")
    print(f"Total entries after: {total_entries_after}")
    print(f"Duplicates removed: {duplicates_removed}")


def main():
    """Main entry point."""
    file_path = Path("data/correct_matches.yaml")
    tags_path = Path("data/competition_tags.yaml")

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    print(f"Loading competition tags from {tags_path}...")
    competition_tags = load_competition_tags(tags_path)
    strip_count = len(competition_tags.get("strip_tags", []))
    preserve_count = len(competition_tags.get("preserve_tags", []))
    print(f"Loaded {strip_count} strip tags and {preserve_count} preserve tags")

    print(f"Cleaning up {file_path}...")
    clean_and_alphabetize_correct_matches(file_path, competition_tags)
    print("Done!")


if __name__ == "__main__":
    main()
