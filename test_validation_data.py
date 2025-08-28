#!/usr/bin/env python3
"""Test validation tool data loading."""

from pathlib import Path
import yaml


def test_data_loading():
    """Test if correct_matches.yaml is being loaded correctly."""

    # Load correct_matches.yaml directly
    correct_matches_path = Path("data/correct_matches.yaml")
    print(f"Loading {correct_matches_path}")

    if not correct_matches_path.exists():
        print("❌ File does not exist")
        return

    try:
        with open(correct_matches_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        print("✅ File loaded successfully")
        print(f"Data type: {type(data)}")
        print(f"Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

        if "brush" in data:
            brush_section = data["brush"]
            print(f"Brush section type: {type(brush_section)}")
            print(
                f"Brush section keys: {list(brush_section.keys()) if isinstance(brush_section, dict) else 'Not a dict'}"
            )

            if "Chisel & Hound" in brush_section:
                ch_hound_section = brush_section["Chisel & Hound"]
                print(f"Chisel & Hound section type: {type(ch_hound_section)}")
                print(
                    f"Chisel & Hound section keys: {list(ch_hound_section.keys()) if isinstance(ch_hound_section, dict) else 'Not a dict'}"
                )

                if "v26" in ch_hound_section:
                    v26_patterns = ch_hound_section["v26"]
                    print(f"v26 patterns type: {type(v26_patterns)}")
                    print(f"v26 patterns: {v26_patterns}")

                    if isinstance(v26_patterns, list):
                        for i, pattern in enumerate(v26_patterns):
                            print(f"  Pattern {i}: {pattern}")
                            if "v27" in pattern.lower():
                                print("    ⚠️  Contains 'v27' but placed under v26!")
                else:
                    print("❌ No v26 section found")
            else:
                print("❌ No Chisel & Hound section found")
        else:
            print("❌ No brush section found")

    except Exception as e:
        print(f"❌ Error loading file: {e}")


if __name__ == "__main__":
    test_data_loading()
