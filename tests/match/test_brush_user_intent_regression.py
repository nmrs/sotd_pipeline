"""
Regression tests to prevent future user intent data loss in correct matches processing.

These tests ensure that any future changes to the brush matcher will not accidentally
remove user intent preservation functionality.
"""

import pytest
from unittest.mock import patch, MagicMock

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.types import create_match_result


class TestBrushUserIntentRegression:
    """Regression tests to prevent future user intent data loss."""

    @pytest.fixture
    def brush_matcher(self):
        """Create a brush matcher instance for testing."""
        return BrushMatcher(debug=True)

    def test_regression_user_intent_always_present_in_correct_matches(self, brush_matcher):
        """
        Regression test: Ensure user_intent is always present in correct match results.

        This test verifies that all correct match processing methods consistently
        include user_intent field, preventing future regressions.
        """
        # Test handle_knot correct match
        value = "G5C Rad Dinosaur Creation"
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
            with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
                mock_split.return_value = ("Rad Dinosaur Creation", "G5C", "smart_analysis")

                result = brush_matcher.match(value)

                assert result is not None
                assert result.matched is not None
                assert "user_intent" in result.matched
                assert result.matched["user_intent"] == "knot_primary"  # G5C appears first

        # Test split_brush correct match
        value = "aka brushworx g5c"
        mock_correct_match = MagicMock()
        mock_correct_match.handle_maker = "AKA Brushworx"
        mock_correct_match.handle_model = None
        mock_correct_match.knot_info = {
            "brand": "AP Shave Co",
            "model": "G5C",
            "fiber": "Synthetic",
            "knot_size_mm": 26.0,
        }
        mock_correct_match.match_type = "split_brush_section"

        with patch.object(
            brush_matcher.correct_matches_checker, "check", return_value=mock_correct_match
        ):
            with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
                mock_split.return_value = ("aka brushworx", "g5c", "smart_analysis")

                result = brush_matcher.match(value)

                assert result is not None
                assert result.matched is not None
                assert "user_intent" in result.matched
                assert (
                    result.matched["user_intent"] == "handle_primary"
                )  # aka brushworx appears first

    def test_regression_detect_user_intent_method_preserved(self, brush_matcher):
        """
        Regression test: Ensure detect_user_intent method is preserved and functional.

        This test verifies that the core user intent detection logic remains intact
        and produces correct results for various scenarios.
        """
        test_cases = [
            # (value, handle_text, knot_text, expected_intent, description)
            ("G5C Rad Dinosaur", "Rad Dinosaur", "G5C", "knot_primary", "knot first"),
            ("Rad Dinosaur G5C", "Rad Dinosaur", "G5C", "handle_primary", "handle first"),
            ("Same Same", "Same", "Same", "handle_primary", "identical positions"),
            ("Handle Only", "Handle Only", "", "handle_primary", "missing knot"),
            ("", "", "", "handle_primary", "empty strings"),
        ]

        for value, handle_text, knot_text, expected_intent, description in test_cases:
            intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)
            assert (
                intent == expected_intent
            ), f"Wrong intent for {description}: expected {expected_intent}, got {intent}"

    def test_regression_correct_matches_never_remove_user_intent(self, brush_matcher):
        """
        Regression test: Ensure correct matches never remove user intent.

        This test verifies that adding brushes to correct_matches.yaml never
        results in data loss compared to automated matching.
        """
        # Test input that would work with both automated and correct match processing
        value = "G5C Rad Dinosaur Creation"

        # First, test with automated matching (dual component)
        with patch.object(brush_matcher, "_check_correct_matches", return_value=None):
            result_automated = brush_matcher.match(value)

            assert result_automated is not None
            assert result_automated.matched is not None
            assert "user_intent" in result_automated.matched
            automated_intent = result_automated.matched["user_intent"]

        # Then, test with correct matches processing
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
            with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
                mock_split.return_value = ("Rad Dinosaur Creation", "G5C", "smart_analysis")

                result_correct = brush_matcher.match(value)

                assert result_correct is not None
                assert result_correct.matched is not None
                assert "user_intent" in result_correct.matched
                correct_intent = result_correct.matched["user_intent"]

        # Verify that correct matches preserve the same user intent
        assert correct_intent == automated_intent, (
            f"Correct matches changed user intent: automated={automated_intent}, "
            f"correct={correct_intent}"
        )

    def test_regression_all_correct_match_methods_include_user_intent(self, brush_matcher):
        """
        Regression test: Ensure all correct match processing methods include user intent.

        This test directly calls each correct match processing method to verify
        they all include user_intent field.
        """
        # Test _process_handle_knot_correct_match
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

        with patch.object(brush_matcher.brush_splitter, "split_handle_and_knot") as mock_split:
            mock_split.return_value = ("Rad Dinosaur Creation", "G5C", "smart_analysis")

            result = brush_matcher._process_handle_knot_correct_match(value, correct_match)
            assert "user_intent" in result.matched, "handle_knot correct match missing user_intent"

        # Test _process_split_brush_correct_match
        value = "aka brushworx g5c"
        correct_match = {"handle": "aka brushworx", "knot": "ap shave co g5c"}

        with patch.object(brush_matcher.correct_matches_checker, "check") as mock_check:
            mock_handle_match = MagicMock()
            mock_handle_match.handle_maker = "AKA Brushworx"
            mock_handle_match.handle_model = None

            mock_knot_match = MagicMock()
            mock_knot_match.knot_info = {
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
            }

            mock_check.side_effect = [mock_handle_match, mock_knot_match]

            result = brush_matcher._process_split_brush_correct_match(value, correct_match)
            assert "user_intent" in result.matched, "split_brush correct match missing user_intent"

        # Test _process_regular_correct_match
        value = "Simpson Chubby 2"
        correct_match = {"brand": "Simpson", "model": "Chubby 2"}

        result = brush_matcher._process_regular_correct_match(value, correct_match)
        assert "user_intent" in result.matched, "regular correct match missing user_intent"

        # Test _process_split_result
        value = "G5C Rad Dinosaur Creation"
        handle_text = "Rad Dinosaur Creation"
        knot_text = "G5C"
        delimiter_type = "smart_analysis"

        with patch.object(brush_matcher.correct_matches_checker, "check", return_value=None):
            with patch.object(brush_matcher.handle_matcher, "match_handle_maker") as mock_handle:
                mock_handle.return_value = {
                    "handle_maker": "Rad Dinosaur",
                    "handle_model": "Creation",
                    "_matched_by": "HandleMatcher",
                    "_pattern": "rad_dinosaur_pattern",
                }

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
                    assert "user_intent" in result.matched, "split_result missing user_intent"

    def test_regression_user_intent_data_type_consistency(self, brush_matcher):
        """
        Regression test: Ensure user_intent field has consistent data type.

        This test verifies that user_intent is always a string with expected values.
        """
        # Test with brushes that go through correct match processing
        test_cases = [
            ("G5C Rad Dinosaur Creation", "knot_primary"),
            ("aka brushworx g5c", "handle_primary"),
        ]

        for input_text, expected_intent in test_cases:
            # Mock correct matches to ensure we test our processing methods
            mock_correct_match = MagicMock()
            mock_correct_match.handle_maker = "Test Maker"
            mock_correct_match.handle_model = "Test Model"
            mock_correct_match.knot_info = {
                "brand": "Test Brand",
                "model": "Test Model",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
            }
            mock_correct_match.match_type = "handle_knot_section"

            with patch.object(
                brush_matcher.correct_matches_checker, "check", return_value=mock_correct_match
            ):
                with patch.object(
                    brush_matcher.brush_splitter, "split_handle_and_knot"
                ) as mock_split:
                    # Mock split to return handle first for handle_primary, knot first for knot_primary
                    if expected_intent == "handle_primary":
                        mock_split.return_value = ("handle text", "knot text", "smart_analysis")
                    else:
                        mock_split.return_value = ("knot text", "handle text", "smart_analysis")

                    result = brush_matcher.match(input_text)

                    assert result is not None
                    assert result.matched is not None
                    assert "user_intent" in result.matched

                    user_intent = result.matched["user_intent"]

                    # Verify data type
                    assert isinstance(
                        user_intent, str
                    ), f"user_intent should be string, got {type(user_intent)}"

                    # Verify valid values
                    assert user_intent in [
                        "handle_primary",
                        "knot_primary",
                    ], f"user_intent should be 'handle_primary' or 'knot_primary', got '{user_intent}'"

    def test_regression_user_intent_preserved_across_pipeline_phases(self, brush_matcher):
        """
        Regression test: Ensure user_intent is preserved when data flows through pipeline.

        This test simulates what happens when brush data moves through different
        pipeline phases to ensure user_intent is not lost.
        """
        value = "G5C Rad Dinosaur Creation"

        # Simulate match phase
        result = brush_matcher.match(value)
        assert "user_intent" in result.matched
        original_intent = result.matched["user_intent"]

        # Simulate data transformation (like what might happen in enrich phase)
        transformed_data = result.matched.copy()
        transformed_data["enriched"] = True
        transformed_data["additional_field"] = "test_value"

        # Verify user_intent is still present and unchanged
        assert "user_intent" in transformed_data
        assert transformed_data["user_intent"] == original_intent

        # Simulate data serialization/deserialization
        import json

        serialized = json.dumps(transformed_data)
        deserialized = json.loads(serialized)

        # Verify user_intent survives serialization
        assert "user_intent" in deserialized
        assert deserialized["user_intent"] == original_intent

    def test_regression_user_intent_edge_cases_handled(self, brush_matcher):
        """
        Regression test: Ensure edge cases in user intent detection are handled correctly.

        This test covers various edge cases to ensure they don't cause errors
        or incorrect user intent values.
        """
        edge_cases = [
            # (value, handle_text, knot_text, expected_intent, description)
            ("", "", "", "handle_primary", "all empty"),
            ("Single", "Single", "", "handle_primary", "handle only"),
            ("", "Handle", "Knot", "handle_primary", "empty value"),
            ("Text", "Text", "Text", "handle_primary", "identical text"),
            ("A B C", "A B", "C", "handle_primary", "handle first"),
            ("A B C", "C", "A B", "knot_primary", "knot first"),
            (
                "Very Long Handle Text With Many Words",
                "Very Long Handle Text",
                "With Many Words",
                "handle_primary",
                "long text",
            ),
        ]

        for value, handle_text, knot_text, expected_intent, description in edge_cases:
            try:
                intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)
                assert (
                    intent == expected_intent
                ), f"Edge case failed: {description} - expected {expected_intent}, got {intent}"
            except Exception as e:
                pytest.fail(f"Edge case threw exception: {description} - {e}")
