#!/usr/bin/env python3
"""Test all unique brush entries from extracted data against brush matcher."""

import json

from sotd.match.brush_matcher import BrushMatcher
from sotd.utils.match_filter_utils import normalize_for_matching


def strip_markdown_links(text: str) -> str:
    """Strip markdown links from text, keeping the link text."""
    import re

    # Remove markdown links like [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove bare URLs (both http and https)
    text = re.sub(r"https?://[^\s]+", "", text)
    return text.strip()


def extract_brush_strings():
    """Extract all unique brush strings from extracted data."""
    with open("data/extracted/2025-06.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    brush_strings = set()
    for record in data.get("data", []):
        if "brush" in record:
            # Strip markdown links first
            brush_string = strip_markdown_links(record["brush"])
            if brush_string:  # Only add non-empty strings
                brush_strings.add(brush_string)

    return sorted(brush_strings)


def test_brush_matcher():
    """Test brush matcher against all extracted brush strings."""
    matcher = BrushMatcher()
    brush_strings = extract_brush_strings()

    print("Testing {} unique brush strings...".format(len(brush_strings)))
    print()

    results = {
        "total": len(brush_strings),
        "successful": 0,
        "unmatched": 0,
        "edge_cases": 0,
        "failures": 0,
        "examples": {
            "successful": [],
            "unmatched": [],
            "edge_cases": [],
            "failures": [],
        },
    }

    for i, brush_string in enumerate(brush_strings):
        try:
            # Simulate what the match phase does: normalize first
            normalized_brush = normalize_for_matching(brush_string, field="brush")

            if not normalized_brush:
                results["edge_cases"] += 1
                if len(results["examples"]["edge_cases"]) < 5:
                    results["examples"]["edge_cases"].append(brush_string)
                continue

            # Now test the normalized string
            result = matcher.match(normalized_brush)

            if result and result.get("matched"):
                results["successful"] += 1
                if len(results["examples"]["successful"]) < 5:
                    results["examples"]["successful"].append(brush_string)
            else:
                results["unmatched"] += 1
                if len(results["examples"]["unmatched"]) < 5:
                    results["examples"]["unmatched"].append(brush_string)

        except Exception as e:
            results["failures"] += 1
            if len(results["examples"]["failures"]) < 5:
                results["examples"]["failures"].append(f"{brush_string} (Error: {e})")

        if (i + 1) % 100 == 0:
            print("Processed {}/{} entries...".format(i + 1, len(brush_strings)))

    # Print results
    print("\nRESULTS:")
    print("Total entries: {}".format(results["total"]))
    success_pct = results["successful"] / results["total"] * 100
    print("Successful matches: {} ({:.1f}%)".format(results["successful"], success_pct))
    unmatched_pct = results["unmatched"] / results["total"] * 100
    print("Unmatched: {} ({:.1f}%)".format(results["unmatched"], unmatched_pct))
    edge_pct = results["edge_cases"] / results["total"] * 100
    print("Edge cases: {} ({:.1f}%)".format(results["edge_cases"], edge_pct))
    failure_pct = results["failures"] / results["total"] * 100
    print("Failures: {} ({:.1f}%)".format(results["failures"], failure_pct))

    print("\nEXAMPLES:")
    print("Successful matches:")
    for example in results["examples"]["successful"]:
        print("  - {}".format(example))

    print("\nUnmatched:")
    for example in results["examples"]["unmatched"]:
        print("  - {}".format(example))

    print("\nEdge cases:")
    for example in results["examples"]["edge_cases"]:
        print("  - {}".format(example))

    print("\nFailures:")
    for example in results["examples"]["failures"]:
        print("  - {}".format(example))

    return results


if __name__ == "__main__":
    results = test_brush_matcher()
    if results["total"] > 0:
        success_rate = results["successful"] / results["total"] * 100
        print(
            f"\nSUMMARY: {results['successful']}/{results['total']} "
            f"({success_rate:.1f}%) successful matches"
        )
    else:
        print("\nSUMMARY: No brush entries found to test")
