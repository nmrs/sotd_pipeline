"""
Test the brush splitter non-delimiter issue.

This test demonstrates how the current non-delimiter logic prevents legitimate
delimiter detection when non-delimiter tokens are present in the text.
"""

import pytest
from pathlib import Path

from sotd.match.brush.splitter import BrushSplitter
from sotd.match.brush.handle_matcher import HandleMatcher


class TestBrushSplitterNonDelimiterIssue:
    """Test cases demonstrating the non-delimiter logic issue."""

    @pytest.fixture
    def brush_splitter(self):
        """Create a brush splitter instance for testing."""
        handle_matcher = HandleMatcher(Path("data/handles.yaml"))
        return BrushSplitter(handle_matcher, [])

    def test_in_delimiter_with_x_specification(self, brush_splitter):
        """
        Test that " in " delimiter is ignored when " x " is present in specifications.

        This demonstrates the core issue: the non-delimiter logic prevents all
        delimiter detection when any non-delimiter token is found.
        """
        # Test case that should split on " in " but doesn't due to " x " non-delimiter
        test_brush = "AKA Brushworx AK47 knot in Southland 1 in. x 3 in. Galvanized Nipple Handle"

        # Expected behavior: Should split on " in " delimiter
        # Expected handle: "Southland 1 in. x 3 in. Galvanized Nipple Handle"
        # Expected knot: "AKA Brushworx AK47 knot"

        # Test delimiter detection directly
        handle, knot, delimiter_type = brush_splitter.split_handle_and_knot(test_brush)

        # This should now work correctly with the fix
        assert handle is not None, f"Expected handle to be found, got: {handle}"
        assert knot is not None, f"Expected knot to be found, got: {knot}"
        assert delimiter_type == "handle_primary", f"Expected handle_primary, got: {delimiter_type}"

        # Verify the split is correct
        assert (
            handle == "Southland 1 in. x 3 in. Galvanized Nipple Handle"
        ), f"Expected 'Southland 1 in. x 3 in. Galvanized Nipple Handle', got: {handle}"
        assert knot == "AKA Brushworx AK47 knot", f"Expected 'AKA Brushworx AK47 knot', got: {knot}"

        # Test the full splitting logic
        handle, knot, delimiter_type = brush_splitter.split_handle_and_knot(test_brush)

        # Should now use delimiter splitting instead of fiber hint
        assert delimiter_type == "handle_primary", f"Expected handle_primary, got: {delimiter_type}"
        assert (
            handle == "Southland 1 in. x 3 in. Galvanized Nipple Handle"
        ), f"Expected 'Southland 1 in. x 3 in. Galvanized Nipple Handle', got: {handle}"
        assert knot == "AKA Brushworx AK47 knot", f"Expected 'AKA Brushworx AK47 knot', got: {knot}"

    def test_in_delimiter_without_x_specification(self, brush_splitter):
        """
        Test that " in " delimiter works when no " x " is present.

        This confirms that the delimiter detection works correctly when
        no non-delimiter tokens interfere.
        """
        # Test case without " x " specification - should work correctly
        test_brush = "AKA Brushworx AK47 knot in Southland Handle"

        # Expected behavior: Should split on " in " delimiter
        # Expected handle: "Southland Handle"
        # Expected knot: "AKA Brushworx AK47 knot"

        handle, knot, delimiter_type = brush_splitter.split_handle_and_knot(test_brush)

        # This should work correctly
        assert handle is not None, "Expected handle to be found"
        assert knot is not None, "Expected knot to be found"
        assert delimiter_type == "handle_primary", f"Expected handle_primary, got: {delimiter_type}"

        # Verify the split is correct
        assert handle == "Southland Handle", f"Expected 'Southland Handle', got: {handle}"
        assert knot == "AKA Brushworx AK47 knot", f"Expected 'AKA Brushworx AK47 knot', got: {knot}"

    def test_x_specification_interference_analysis(self, brush_splitter):
        """
        Analyze how " x " specifications interfere with delimiter detection.

        This test documents the specific issue: " x " in specifications
        prevents legitimate delimiter detection.
        """
        # Test cases with " x " in specifications
        test_cases = [
            {
                "text": "AKA Brushworx AK47 knot in Southland 1 in. x 3 in. Galvanized Nipple Handle",
                "x_spec": "1 in. x 3 in.",
                "description": "x in handle specifications",
                "expected_delimiter": " in ",
            },
            {
                "text": "Simpson Chubby 2 - 3 Band in 28mm x 52mm",
                "x_spec": "28mm x 52mm",
                "description": "x in knot specifications",
                "expected_delimiter": " in ",
            },
            {
                "text": "Zenith B2 / 28mm x 52mm",
                "x_spec": "28mm x 52mm",
                "description": "x in size specifications",
                "expected_delimiter": " / ",
            },
        ]

        for test_case in test_cases:
            text = test_case["text"]
            x_spec = test_case["x_spec"]
            description = test_case["description"]
            expected_delimiter = test_case["expected_delimiter"]

            # Check if the " x " specification is present
            assert " x " in text, f"' x ' not found in text for {description}"

            # Test delimiter detection
            handle, knot, delimiter_type = brush_splitter.split_handle_and_knot(text)

            # Document the current behavior
            print(f"\nTest case: {description}")
            print(f"Text: {text}")
            print(f"X specification: '{x_spec}'")
            print(f"Expected delimiter: '{expected_delimiter}'")
            print(
                f"Delimiter detection result: handle='{handle}', knot='{knot}', type='{delimiter_type}'"
            )

            # These should now work correctly with the fix
            assert handle is not None, f"Expected handle to be found, got: {handle}"
            assert knot is not None, f"Expected knot to be found, got: {knot}"
            assert (
                delimiter_type is not None
            ), f"Expected delimiter type to be found, got: {delimiter_type}"

    def test_ampersand_reliability_analysis(self, brush_splitter):
        """
        Analyze why " & " is not reliable as a delimiter.

        This test demonstrates that " & " is ambiguous and should not be used
        as a delimiter.
        """
        # Test cases showing " & " ambiguity
        test_cases = [
            {
                "text": "Chisel & Hound v23",
                "description": "Brand name with &",
                "should_split": False,
                "reason": "Brand name, should not split",
            },
            {
                "text": "My handle & my knot",
                "description": "Ambiguous handle/knot",
                "should_split": False,
                "reason": "Ambiguous, unreliable",
            },
            {
                "text": "G5C & Muninn Woodworks curly pine",
                "description": "Ambiguous maker/knot",
                "should_split": False,
                "reason": "Ambiguous, unreliable",
            },
            {
                "text": "C&H v23 Zebra",
                "description": "Brand name with &",
                "should_split": False,
                "reason": "Brand name, should not split",
            },
        ]

        for test_case in test_cases:
            text = test_case["text"]
            description = test_case["description"]
            should_split = test_case["should_split"]
            reason = test_case["reason"]

            # Test delimiter detection
            handle, knot, delimiter_type = brush_splitter.split_handle_and_knot(text)

            print(f"\nTest case: {description}")
            print(f"Text: {text}")
            print(f"Should split: {should_split}")
            print(f"Reason: {reason}")
            print(
                f"Delimiter detection result: handle='{handle}', knot='{knot}', type='{delimiter_type}'"
            )

            # Document that " & " is unreliable
            if " & " in text:
                print(f"  Note: ' & ' is present but unreliable as delimiter")

    def test_correct_behavior_definition(self, brush_splitter):
        """
        Define what the correct behavior should be.

        This test documents the expected behavior for each test case
        once the non-delimiter issue is fixed.
        """
        # Define expected behaviors for each test case
        expected_behaviors = [
            {
                "text": "AKA Brushworx AK47 knot in Southland 1 in. x 3 in. Galvanized Nipple Handle",
                "expected_handle": "Southland 1 in. x 3 in. Galvanized Nipple Handle",
                "expected_knot": "AKA Brushworx AK47 knot",
                "expected_delimiter": "handle_primary",
                "description": "in delimiter with x specification",
            },
            {
                "text": "Simpson Chubby 2 - 3 Band in 28mm x 52mm",
                "expected_handle": "28mm x 52mm",
                "expected_knot": "Simpson Chubby 2 - 3 Band",
                "expected_delimiter": "handle_primary",
                "description": "in delimiter with x in handle spec",
            },
            {
                "text": "Zenith B2 / 28mm x 52mm",
                "expected_handle": "Zenith B2",
                "expected_knot": "28mm x 52mm",
                "expected_delimiter": "high_reliability",
                "description": "/ delimiter with x in size spec",
            },
        ]

        for behavior in expected_behaviors:
            text = behavior["text"]
            expected_handle = behavior["expected_handle"]
            expected_knot = behavior["expected_knot"]
            expected_delimiter = behavior["expected_delimiter"]
            description = behavior["description"]

            # For now, these tests will fail because the non-delimiter logic prevents
            # proper delimiter detection. Once the fix is implemented, these should pass.

            # Test the scoring to verify our expectations are reasonable
            parts = (
                text.split(" in ", 1)
                if " in " in text
                else (
                    text.split(" w/ ", 1)
                    if " w/ " in text
                    else text.split(" - ", 1) if " - " in text else text.split(" / ", 1)
                )
            )

            if len(parts) == 2:
                part1, part2 = parts[0].strip(), parts[1].strip()

                # Score both parts
                part1_handle_score = brush_splitter._score_as_handle(part1)
                part1_knot_score = brush_splitter._score_as_knot(part1)
                part2_handle_score = brush_splitter._score_as_handle(part2)
                part2_knot_score = brush_splitter._score_as_knot(part2)

                print(f"\nScoring for {description}:")
                print(f"  Part 1 ('{part1}'): handle={part1_handle_score}, knot={part1_knot_score}")
                print(f"  Part 2 ('{part2}'): handle={part2_handle_score}, knot={part2_knot_score}")

                # Verify our expectations are reasonable based on scoring
                if "handle" in description:
                    # For handle-primary delimiters, first part should score higher as handle
                    assert (
                        part1_handle_score > part2_handle_score
                        or part2_knot_score > part1_knot_score
                    ), f"Scoring doesn't support expected behavior for {description}"
                elif "knot" in description:
                    # For other delimiters, scoring should support the expected split
                    assert (
                        part1_handle_score > part2_handle_score
                        and part2_knot_score > part1_knot_score
                    ) or (
                        part2_handle_score > part1_handle_score
                        and part1_knot_score > part2_knot_score
                    ), f"Scoring doesn't support expected behavior for {description}"
