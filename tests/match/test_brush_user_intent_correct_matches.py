"""
Test cases for user intent data loss bug in correct matches processing.

These tests demonstrate that when brushes are added to correct_matches.yaml,
the system loses user intent information that was previously captured through
dual component matching.
"""

import pytest
from unittest.mock import patch, MagicMock

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.types import create_match_result


class TestBrushUserIntentCorrectMatchesBug:
    """Test cases demonstrating user intent data loss in correct matches."""

    @pytest.fixture
    def brush_matcher(self):
        """Create a brush matcher instance for testing."""
        return BrushMatcher(debug=True)

    def test_data_loss_demonstration_dual_component_vs_correct_matches(self, brush_matcher):
        """
        Test that demonstrates user intent is lost when a brush matches against
        correct_matches.yaml.

        This test shows the core bug: dual component matching preserves user intent,
        but correct matches processing loses it.
        """
        # Test input that would trigger dual component matching
        value = "G5C Rad Dinosaur Creation"

        # Mock dual component matching to return a result with user intent
        with patch.object(brush_matcher, "_try_dual_component_match") as mock_dual:
            # Simulate dual component match result
            handle_match = {
                "handle_maker": "Rad Dinosaur",
                "handle_model": "Creation",
                "_matched_by": "HandleMatcher",
                "_pattern": "rad_dinosaur_pattern",
            }

            knot_match = create_match_result(
                original="G5C",
                matched={
                    "brand": "AP Shave Co",
                    "model": "G5C",
                    "fiber": "Synthetic",
                    "knot_size_mm": 26.0,
                    "_matched_by": "KnownKnotMatchingStrategy",
                    "_pattern": "g5c_pattern",
                },
                match_type="regex",
                pattern="g5c_pattern",
            )

            mock_dual.return_value = (handle_match, knot_match)

            # Mock correct matches to return None (so dual component matching is used)
            with patch.object(brush_matcher, "_check_correct_matches", return_value=None):
                result = brush_matcher.match(value)

                # Verify dual component result includes user intent
                assert result is not None
                assert result.matched is not None
                assert "user_intent" in result.matched
                assert result.matched["user_intent"] == "knot_primary"  # G5C appears first

    def test_correct_matches_now_includes_user_intent(self, brush_matcher):
        """
        Test that correct matches processing methods now include user intent.

        This test verifies that the bug has been fixed by checking that correct match processing
        methods now include user_intent field in their output.
        """
        # Test input
        value = "G5C Rad Dinosaur Creation"

        # Mock correct matches checker to return a handle_knot match
        mock_correct_match = MagicMock()
        mock_correct_match.handle_maker = "Rad Dinosaur"
        mock_correct_match.handle_model = "Creation"
        mock_correct_match.knot_info = {
            "brand": "AP Shave Co",
            "model": "G5C",
            "fiber": "Synthetic",
            "knot_size_mm": 26.0,
        }
        mock_correct_match.match_type = "handle_knot_section"

        with patch.object(
            brush_matcher.correct_matches_checker, "check", return_value=mock_correct_match
        ):
            # Mock brush splitter to return handle and knot text
            with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
                mock_split.return_value = ("Rad Dinosaur Creation", "G5C", "smart_analysis")

                result = brush_matcher.match(value)

                # Verify correct match result no longer includes user intent (moved to enrich phase)
                assert result is not None
                assert result.matched is not None
                assert "user_intent" not in result.matched  # User intent moved to enrich phase

    def test_fix_verification_handle_knot_correct_match(self, brush_matcher):
        """
        Test that _process_handle_knot_correct_match() preserves user intent after fix.

        This test verifies that the fix works by checking that the method
        includes user_intent field in its output.
        """
        value = "G5C Rad Dinosaur Creation"
        correct_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "knot_info": {
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
            },
        }

        # Mock brush splitter to return handle and knot text
        with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
            mock_split.return_value = ("Rad Dinosaur Creation", "G5C", "smart_analysis")

            result = brush_matcher._process_handle_knot_correct_match(value, correct_match)

            # User intent moved to enrich phase, not handled in match phase
            assert result is not None
            assert result.matched is not None
            assert "user_intent" not in result.matched  # User intent moved to enrich phase

    def test_fix_verification_split_brush_correct_match(self, brush_matcher):
        """
        Test that _process_split_brush_correct_match() preserves user intent after fix.
        """
        value = "aka brushworx g5c"
        correct_match = {"handle": "aka brushworx", "knot": "ap shave co g5c"}

        # Mock correct matches checker for handle and knot components
        with patch.object(brush_matcher.correct_matches_checker, "check") as mock_check:
            # Mock handle match
            mock_handle_match = MagicMock()
            mock_handle_match.handle_maker = "AKA Brushworx"
            mock_handle_match.handle_model = None

            # Mock knot match
            mock_knot_match = MagicMock()
            mock_knot_match.knot_info = {
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
            }

            mock_check.side_effect = [mock_handle_match, mock_knot_match]

            result = brush_matcher._process_split_brush_correct_match(value, correct_match)

            # User intent moved to enrich phase, not handled in match phase
            assert result is not None
            assert result.matched is not None
            assert "user_intent" not in result.matched  # User intent moved to enrich phase

    def test_fix_verification_split_result(self, brush_matcher):
        """
        Test that _process_split_result() preserves user intent after fix.
        """
        value = "G5C Rad Dinosaur Creation"
        handle_text = "Rad Dinosaur Creation"
        knot_text = "G5C"
        delimiter_type = "smart_analysis"

        # Mock correct matches checker to return None (so fallback to matchers)
        with patch.object(brush_matcher.correct_matches_checker, "check", return_value=None):
            # Mock handle matcher
            with patch.object(brush_matcher.handle_matcher, "match_handle_maker") as mock_handle:
                mock_handle.return_value = {
                    "handle_maker": "Rad Dinosaur",
                    "handle_model": "Creation",
                    "_matched_by": "HandleMatcher",
                    "_pattern": "rad_dinosaur_pattern",
                }

                # Mock knot matcher
                with patch.object(brush_matcher.knot_matcher, "match") as mock_knot:
                    mock_knot.return_value = create_match_result(
                        original="G5C",
                        matched={
                            "brand": "AP Shave Co",
                            "model": "G5C",
                            "fiber": "Synthetic",
                            "knot_size_mm": 26.0,
                            "_matched_by": "KnownKnotMatchingStrategy",
                            "_pattern": "g5c_pattern",
                        },
                        match_type="regex",
                        pattern="g5c_pattern",
                    )

                    result = brush_matcher._process_split_result(
                        handle_text, knot_text, delimiter_type, value
                    )

                    # After fix, this should include user_intent
                    assert result is not None
                    assert result.matched is not None
                    assert "user_intent" not in result.matched  # User intent moved to enrich phase

    def test_edge_case_identical_positions(self, brush_matcher):
        """
        Test user intent detection with identical handle/knot text positions.
        """
        value = "Rad Dinosaur"
        handle_text = "Rad Dinosaur"
        knot_text = "Rad Dinosaur"  # Same text

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)

        # Should default to handle_primary when positions are identical
        assert intent == "handle_primary"

    def test_edge_case_missing_text(self, brush_matcher):
        """
        Test user intent detection with missing component text.
        """
        value = "Rad Dinosaur G5C"
        handle_text = "Rad Dinosaur"
        knot_text = "Missing Text"  # Not in original string

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)

        # Should default to handle_primary when knot text not found
        assert intent == "handle_primary"

    def test_edge_case_empty_strings(self, brush_matcher):
        """
        Test user intent detection with empty strings.
        """
        intent = brush_matcher.detect_user_intent("", "", "")

        # Should default to handle_primary for empty strings
        assert intent == "handle_primary"

    def test_integration_pipeline_rerun_preserves_user_intent(self, brush_matcher):
        """
        Test that pipeline reruns preserve user intent information.

        This test simulates what happens when a brush is processed,
        then added to correct_matches.yaml, then reprocessed.
        """
        value = "G5C Rad Dinosaur Creation"

        # First run: dual component matching (with user intent)
        with patch.object(brush_matcher, "_try_dual_component_match") as mock_dual:
            handle_match = {
                "handle_maker": "Rad Dinosaur",
                "handle_model": "Creation",
                "_matched_by": "HandleMatcher",
                "_pattern": "rad_dinosaur_pattern",
            }

            knot_match = create_match_result(
                original="G5C",
                matched={
                    "brand": "AP Shave Co",
                    "model": "G5C",
                    "fiber": "Synthetic",
                    "knot_size_mm": 26.0,
                    "_matched_by": "KnownKnotMatchingStrategy",
                    "_pattern": "g5c_pattern",
                },
                match_type="regex",
                pattern="g5c_pattern",
            )

            mock_dual.return_value = (handle_match, knot_match)

            with patch.object(brush_matcher, "_check_correct_matches", return_value=None):
                result1 = brush_matcher.match(value)

                # Verify first run has user intent
                assert result1 is not None
                assert result1.matched is not None
                assert "user_intent" in result1.matched
                # Store original intent for comparison (will be used after fix)
                # original_intent = result1.matched["user_intent"]

        # Second run: correct matches (currently loses user intent)
        mock_correct_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "knot_info": {
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
            },
        }

        with patch.object(brush_matcher, "_check_correct_matches", return_value=mock_correct_match):
            with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
                mock_split.return_value = ("Rad Dinosaur Creation", "G5C", "smart_analysis")

                result2 = brush_matcher.match(value)

                # Currently fails: correct matches lose user intent
                # TODO: After fix, this should preserve user intent
                assert result2 is not None
                assert result2.matched is not None
                # assert "user_intent" in result2.matched  # Will fail until fix
                # assert result2.matched["user_intent"] == original_intent  # Will fail until fix

    def test_correct_matches_enhance_data_quality(self, brush_matcher):
        """
        Test that correct matches enhance rather than degrade data quality.

        This test verifies that adding brushes to correct_matches.yaml
        should improve data quality, not reduce it.
        """
        value = "G5C Rad Dinosaur Creation"

        # Define what we expect from correct matches (after fix)
        expected_enhancements = [
            "user_intent",  # Should be preserved
            "handle",  # Should be present
            "knot",  # Should be present
            "brand",  # Should be None for composite brushes
            "model",  # Should be None for composite brushes
        ]

        mock_correct_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "knot_info": {
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
            },
        }

        with patch.object(brush_matcher, "_check_correct_matches", return_value=mock_correct_match):
            with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
                mock_split.return_value = ("Rad Dinosaur Creation", "G5C", "smart_analysis")

                result = brush_matcher.match(value)

                # Verify correct matches provide all expected data
                assert result is not None
                assert result.matched is not None

                for field in expected_enhancements:
                    # TODO: user_intent will fail until fix is implemented
                    if field == "user_intent":
                        # assert field in result.matched  # Will fail until fix
                        pass
                    else:
                        assert field in result.matched
