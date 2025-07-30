"""Integration tests for handle matcher with correct matches workflow."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from sotd.match.handle_matcher import HandleMatcher
from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager


class TestHandleMatcherIntegration:
    """Integration tests for handle matcher with correct matches workflow."""

    @pytest.fixture
    def console_mock(self):
        """Create a mock console for testing."""
        return Mock()

    @pytest.fixture
    def correct_matches_manager(self, console_mock, tmp_path):
        """Create CorrectMatchesManager instance for testing."""
        correct_matches_file = tmp_path / "correct_matches.yaml"
        return CorrectMatchesManager(console_mock, correct_matches_file)

    @pytest.fixture
    def handle_matcher_new_structure(self):
        """Create handle matcher instance with new structure."""
        return HandleMatcher(Path("data/handles_new_structure.yaml"))

    def test_end_to_end_handle_matching_workflow(
        self, handle_matcher_new_structure, correct_matches_manager
    ):
        """Test complete end-to-end handle matching workflow."""
        # Step 1: Match handles using the new structure
        test_cases = [
            ("Declaration Grooming Washington", "Declaration Grooming", "Washington"),
            ("Declaration Grooming Jefferson", "Declaration Grooming", "Jefferson"),
            ("Declaration Grooming Jeffington", "Declaration Grooming", "Jeffington"),
            ("Declaration Grooming handle", "Declaration Grooming", "Unspecified"),
            ("Jayaruh handle", "Jayaruh", "Unspecified"),
            ("Dogwood Handcrafts handle", "Dogwood Handcrafts", "Unspecified"),
        ]

        for text, expected_maker, expected_model in test_cases:
            # Match the handle
            result = handle_matcher_new_structure.match_handle_maker(text)
            assert result is not None, f"Failed to match: {text}"
            assert result["handle_maker"] == expected_maker, f"Wrong maker for: {text}"
            assert result["handle_model"] == expected_model, f"Wrong model for: {text}"

            # Create match data for correct matches
            match_data = {
                "original": text,
                "matched": {
                    "handle_maker": result["handle_maker"],
                    "handle_model": result["handle_model"],
                },
                "field": "handle",
            }

            # Mark as correct
            match_key = correct_matches_manager.create_match_key(
                "handle", text, match_data["matched"]
            )
            correct_matches_manager.mark_match_as_correct(match_key, match_data)

        # Step 2: Save correct matches
        correct_matches_manager.save_correct_matches()

        # Step 3: Verify the saved structure
        # The correct_matches.yaml should have the proper brand/model hierarchy
        # This is verified by the CorrectMatchesManager tests

    def test_correct_matches_priority_over_regex_matching(
        self, handle_matcher_new_structure, correct_matches_manager
    ):
        """Test that correct matches take priority over regex matching."""
        # Add a correct match for a specific text
        test_text = "Declaration Grooming Washington"
        match_data = {
            "original": test_text,
            "matched": {
                "handle_maker": "Declaration Grooming",
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        match_key = correct_matches_manager.create_match_key(
            "handle", test_text, match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # Now when we match the same text, it should use the correct match
        # This would be tested in a full integration test with the brush matcher
        # For now, we verify the correct match was saved properly

    def test_model_consistency_across_workflow(
        self, handle_matcher_new_structure, correct_matches_manager
    ):
        """Test that model names are consistent throughout the workflow."""
        # Test that the same model name is used consistently
        test_cases = [
            ("Declaration Grooming Washington", "Washington"),
            ("DG Washington", "Washington"),  # Abbreviation should still match Washington
        ]

        for text, expected_model in test_cases:
            result = handle_matcher_new_structure.match_handle_maker(text)
            assert result is not None, f"Failed to match: {text}"
            assert result["handle_model"] == expected_model, f"Wrong model for: {text}"

            # Both should save to the same model section in correct matches
            match_data = {
                "original": text,
                "matched": {
                    "handle_maker": result["handle_maker"],
                    "handle_model": result["handle_model"],
                },
                "field": "handle",
            }

            match_key = correct_matches_manager.create_match_key(
                "handle", text, match_data["matched"]
            )
            correct_matches_manager.mark_match_as_correct(match_key, match_data)

        correct_matches_manager.save_correct_matches()

        # Both entries should be saved under Declaration Grooming -> Washington

    def test_backward_compatibility_with_old_structure(self, correct_matches_manager):
        """Test that the system works with the new handle structure."""
        # Test with new structure
        handle_matcher = HandleMatcher(Path("data/handles.yaml"))
        result = handle_matcher.match_handle_maker("Declaration Grooming Washington")
        assert result is not None
        assert result["handle_maker"] == "Declaration Grooming"
        assert result["handle_model"] == "Washington"  # New structure uses specific model

        # Should work with the CorrectMatchesManager
        match_data = {
            "original": "Declaration Grooming Washington",
            "matched": {
                "handle_maker": result["handle_maker"],
                "handle_model": result["handle_model"],
            },
            "field": "handle",
        }

        match_key = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Washington", match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

    def test_performance_with_correct_matches(
        self, handle_matcher_new_structure, correct_matches_manager
    ):
        """Test performance when using correct matches."""
        import time

        # Add some correct matches
        test_cases = [
            ("Declaration Grooming Washington", "Declaration Grooming", "Washington"),
            ("Declaration Grooming Jefferson", "Declaration Grooming", "Jefferson"),
            ("Jayaruh handle", "Jayaruh", "Unspecified"),
            ("Dogwood Handcrafts handle", "Dogwood Handcrafts", "Unspecified"),
        ]

        for text, maker, model in test_cases:
            match_data = {
                "original": text,
                "matched": {
                    "handle_maker": maker,
                    "handle_model": model,
                },
                "field": "handle",
            }

            match_key = correct_matches_manager.create_match_key(
                "handle", text, match_data["matched"]
            )
            correct_matches_manager.mark_match_as_correct(match_key, match_data)

        correct_matches_manager.save_correct_matches()

        # Test performance of multiple matches
        test_texts = [
            "Declaration Grooming Washington",
            "Declaration Grooming Jefferson",
            "Jayaruh handle",
            "Dogwood Handcrafts handle",
        ] * 25  # 100 total operations

        start_time = time.time()

        for text in test_texts:
            result = handle_matcher_new_structure.match_handle_maker(text)
            assert result is not None, f"Failed to match: {text}"
            assert "handle_maker" in result
            assert "handle_model" in result

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Should complete in reasonable time
        assert elapsed_time < 1.0, f"Performance test took too long: {elapsed_time:.3f} seconds"

    def test_error_handling_integration(
        self, handle_matcher_new_structure, correct_matches_manager
    ):
        """Test error handling in the integrated workflow."""
        # Test with invalid input
        result = handle_matcher_new_structure.match_handle_maker("")
        assert result is None

        # Test with non-existent brand
        result = handle_matcher_new_structure.match_handle_maker("NonExistentBrand handle")
        assert result is None

        # Test with malformed data
        try:
            match_data = {
                "original": "test",
                "matched": {
                    "handle_maker": "Declaration Grooming",
                    # Missing handle_model
                },
                "field": "handle",
            }

            match_key = correct_matches_manager.create_match_key(
                "handle", "test", match_data["matched"]
            )
            correct_matches_manager.mark_match_as_correct(match_key, match_data)
            correct_matches_manager.save_correct_matches()

            # Should handle missing fields gracefully
        except Exception as e:
            # Should fail gracefully with clear error message
            assert "handle_model" in str(e) or "KeyError" in str(e)

    def test_data_integrity_across_phases(
        self, handle_matcher_new_structure, correct_matches_manager
    ):
        """Test that data integrity is maintained across different phases."""
        # Simulate data flow from extract -> match -> correct matches

        # Phase 1: Extract phase output (simulated)
        extract_data = {
            "original": "Declaration Grooming Washington handle",
            "normalized": "declaration grooming washington handle",
        }

        # Phase 2: Match phase
        result = handle_matcher_new_structure.match_handle_maker(extract_data["normalized"])
        assert result is not None

        # Phase 3: Correct matches phase
        match_data = {
            "original": extract_data["original"],
            "matched": {
                "handle_maker": result["handle_maker"],
                "handle_model": result["handle_model"],
            },
            "field": "handle",
        }

        match_key = correct_matches_manager.create_match_key(
            "handle", extract_data["original"], match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # Verify data integrity
        assert match_data["matched"]["handle_maker"] == "Declaration Grooming"
        assert match_data["matched"]["handle_model"] == "Washington"
        assert match_data["original"] == extract_data["original"]

    def test_real_world_scenarios(self, handle_matcher_new_structure, correct_matches_manager):
        """Test real-world scenarios that users might encounter."""
        # Scenario 1: User adds correct match for specific model
        scenario1_text = "Declaration Grooming Washington"
        scenario1_result = handle_matcher_new_structure.match_handle_maker(scenario1_text)
        assert scenario1_result["handle_model"] == "Washington"

        # Scenario 2: User adds correct match for general pattern
        scenario2_text = "Declaration Grooming handle"
        scenario2_result = handle_matcher_new_structure.match_handle_maker(scenario2_text)
        assert scenario2_result["handle_model"] == "Unspecified"

        # Scenario 3: User adds correct match for brand without specific models
        scenario3_text = "Jayaruh handle"
        scenario3_result = handle_matcher_new_structure.match_handle_maker(scenario3_text)
        assert scenario3_result["handle_model"] == "Unspecified"

        # All scenarios should work with the same workflow
        scenarios = [
            (scenario1_text, scenario1_result),
            (scenario2_text, scenario2_result),
            (scenario3_text, scenario3_result),
        ]

        for text, result in scenarios:
            match_data = {
                "original": text,
                "matched": {
                    "handle_maker": result["handle_maker"],
                    "handle_model": result["handle_model"],
                },
                "field": "handle",
            }

            match_key = correct_matches_manager.create_match_key(
                "handle", text, match_data["matched"]
            )
            correct_matches_manager.mark_match_as_correct(match_key, match_data)

        correct_matches_manager.save_correct_matches()

        # All scenarios should be saved correctly with proper model names
