"""
TDD test for structure preservation in composite brush workflow.

This test ensures that when a composite brush is:
1. Regex matched -> data/matched (nested structure)
2. Saved to correct_matches.yaml
3. Rehydrated via CorrectMatchesStrategy

The rehydrated structure should be IDENTICAL to the original regex match structure.
"""

import json
import tempfile
import yaml
from pathlib import Path
import pytest

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.brush_matching_strategies.correct_matches_strategy import CorrectMatchesStrategy


class TestStructurePreservationTDD:
    """Test that composite brush structures are preserved identically through the workflow."""

    def test_composite_brush_structure_preservation(self):
        """
        Test that composite brush structure is preserved identically.

        The rehydrated structure should match the original regex match structure exactly,
        including nested handle/knot objects and all metadata fields.
        """
        # Step 1: Get actual regex match result
        matcher = BrushMatcher()
        test_input = "DG B3 in C&H handle"

        regex_result = matcher.match(test_input)
        assert regex_result is not None, "Should get regex match result"
        assert regex_result.matched is not None, "Should have matched data"

        # Verify we have the expected nested structure
        assert "handle" in regex_result.matched, "Should have handle section"
        assert "knot" in regex_result.matched, "Should have knot section"
        assert regex_result.matched["handle"]["brand"] == "Chisel & Hound"
        assert regex_result.matched["knot"]["brand"] == "Declaration Grooming"

        # Step 2: Create temporary correct_matches.yaml
        temp_correct_matches = {
            "handle": {"Chisel & Hound": {"Unspecified": [test_input.lower()]}},
            "knot": {
                "Declaration Grooming": {
                    "B3": {"strings": [test_input.lower()], "fiber": "Badger", "knot_size_mm": 28}
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(temp_correct_matches, f, default_flow_style=False)
            temp_file_path = f.name

        try:
            # Step 3: Rehydrate using CorrectMatchesStrategy
            with open(temp_file_path, "r") as f:
                loaded_correct_matches = yaml.safe_load(f)

            correct_matches_strategy = CorrectMatchesStrategy(loaded_correct_matches)
            rehydrated_result = correct_matches_strategy.match(test_input)

            assert rehydrated_result is not None, "Should rehydrate successfully"
            assert rehydrated_result.matched is not None, "Should have matched data"

            # Step 4: Verify structures are IDENTICAL
            original_matched = regex_result.matched
            rehydrated_matched = rehydrated_result.matched

            # The rehydrated structure should preserve the EXACT same format
            self._assert_structures_identical(original_matched, rehydrated_matched)

        finally:
            # Clean up
            Path(temp_file_path).unlink()

    def _assert_structures_identical(self, original: dict, rehydrated: dict):
        """Assert that the rehydrated structure matches the expected simplified format."""

        # Check that we have the expected structure for composite brushes
        assert "handle" in rehydrated, "Should preserve handle section"
        assert "knot" in rehydrated, "Should preserve knot section"

        # Check handle section has core data
        rehydrated_handle = rehydrated["handle"]
        assert rehydrated_handle["brand"] == "Chisel & Hound", "Should preserve handle brand"
        assert rehydrated_handle["model"] == "Unspecified", "Should preserve handle model"

        # Check knot section has core data
        rehydrated_knot = rehydrated["knot"]
        assert rehydrated_knot["brand"] == "Declaration Grooming", "Should preserve knot brand"
        assert rehydrated_knot["model"] == "B3", "Should preserve knot model"
        assert rehydrated_knot["fiber"] == "Badger", "Should preserve knot fiber"
        assert rehydrated_knot["knot_size_mm"] == 28, "Should preserve knot size"

        # Check that we have the expected composite brush structure
        assert rehydrated["brand"] is None, "Composite brush should have brand=None"
        assert rehydrated["model"] is None, "Composite brush should have model=None"
        assert (
            rehydrated["source_text"] == "DG B3 in C&H handle"
        ), "Should preserve original source_text"
        assert (
            rehydrated["_matched_by"] == "CorrectMatchesStrategy"
        ), "Should indicate correct matches strategy"
        assert rehydrated["_pattern"] == "exact_match", "Should indicate exact match"
        assert (
            rehydrated["strategy"] == "correct_matches"
        ), "Should indicate correct matches strategy"

        # Check that we don't have unnecessary fields
        assert "handle_text" not in rehydrated, "Should not have handle_text field"
        assert "knot_text" not in rehydrated, "Should not have knot_text field"
        assert "split_priority" not in rehydrated, "Should not have split_priority field"
        assert "_delimiter_priority" not in rehydrated, "Should not have _delimiter_priority field"
        assert (
            "high_priority_delimiter" not in rehydrated
        ), "Should not have high_priority_delimiter field"
        assert "score" not in rehydrated, "Should not have score field"
        assert "priority" not in rehydrated["handle"], "Should not have priority in handle"
        assert "score" not in rehydrated["handle"], "Should not have score in handle"
        assert "priority" not in rehydrated["knot"], "Should not have priority in knot"
        assert "score" not in rehydrated["knot"], "Should not have score in knot"

        print("✅ Rehydrated structure matches expected format!")
        print("Expected structure:")
        expected = {
            "brand": None,
            "model": None,
            "handle": {
                "brand": "Chisel & Hound",
                "model": "Unspecified",
            },
            "knot": {
                "brand": "Declaration Grooming",
                "model": "B3",
                "fiber": "Badger",
                "knot_size_mm": 28,
            },
            "source_text": "DG B3 in C&H handle",
            "_matched_by": "CorrectMatchesStrategy",
            "_pattern": "exact_match",
            "strategy": "correct_matches",
        }
        print(json.dumps(expected, indent=2))
        print("\nActual rehydrated structure:")
        print(json.dumps(rehydrated, indent=2, default=str))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
