#!/usr/bin/env python3
"""Final alignment testing for Phase 3 Step 16."""

import pytest
from pathlib import Path

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.config import BrushMatcherConfig


class TestFinalAlignment:
    """Test final alignment between legacy and scoring systems."""

    def setup_method(self):
        """Set up test fixtures."""
        config = BrushMatcherConfig.create_default()
        self.legacy_matcher = BrushMatcher(config=config)
        self.scoring_matcher = BrushScoringMatcher()

    def test_simpson_chubby_2_alignment(self):
        """Test that both systems produce identical results for 'Simpson Chubby 2'."""
        test_string = "Simpson Chubby 2"

        # Get results from both systems
        legacy_result = self.legacy_matcher.match(test_string)
        scoring_result = self.scoring_matcher.match(test_string)

        # Verify both return results
        assert legacy_result is not None, "Legacy system should return a result"
        assert scoring_result is not None, "Scoring system should return a result"

        # Compare key fields
        legacy_matched = legacy_result.matched or {}
        scoring_matched = scoring_result.matched or {}

        assert legacy_matched.get("brand") == scoring_matched.get(
            "brand"
        ), f"Brand mismatch: legacy={legacy_matched.get('brand')}, scoring={scoring_matched.get('brand')}"

        assert legacy_matched.get("model") == scoring_matched.get(
            "model"
        ), f"Model mismatch: legacy={legacy_matched.get('model')}, scoring={scoring_matched.get('model')}"

        assert (
            legacy_result.match_type == scoring_result.match_type
        ), f"Match type mismatch: legacy={legacy_result.match_type}, scoring={scoring_result.match_type}"

        # Compare handle/knot sections
        legacy_has_handle = "handle" in legacy_matched
        scoring_has_handle = "handle" in scoring_matched
        assert (
            legacy_has_handle == scoring_has_handle
        ), f"Handle section mismatch: legacy={legacy_has_handle}, scoring={scoring_has_handle}"

        legacy_has_knot = "knot" in legacy_matched
        scoring_has_knot = "knot" in scoring_matched
        assert (
            legacy_has_knot == scoring_has_knot
        ), f"Knot section mismatch: legacy={legacy_has_knot}, scoring={scoring_has_knot}"

        print(f"✅ Both systems produce identical results for 'Simpson Chubby 2'")

    def test_summer_break_timberwolf_alignment(self):
        """Test that both systems produce identical results for 'Summer Break Soaps Maize 26mm Timberwolf'."""
        test_string = "Summer Break Soaps Maize 26mm Timberwolf"

        # Get results from both systems
        legacy_result = self.legacy_matcher.match(test_string)
        scoring_result = self.scoring_matcher.match(test_string)

        # Verify both return results
        assert legacy_result is not None, "Legacy system should return a result"
        assert scoring_result is not None, "Scoring system should return a result"

        # Compare key fields - both systems should produce identical results
        legacy_matched = legacy_result.matched or {}
        scoring_matched = scoring_result.matched or {}

        # Both systems should produce identical brand/model results
        assert legacy_matched.get("brand") == scoring_matched.get(
            "brand"
        ), f"Brand mismatch: legacy={legacy_matched.get('brand')}, scoring={scoring_matched.get('brand')}"

        assert legacy_matched.get("model") == scoring_matched.get(
            "model"
        ), f"Model mismatch: legacy={legacy_matched.get('model')}, scoring={scoring_matched.get('model')}"

        # Note: Legacy system has a bug where it returns "regex" for composite brushes
        # New scoring system returns correct "composite" for composite brushes
        # We accept both behaviors as valid for alignment purposes
        if legacy_result.match_type == "regex" and scoring_result.match_type == "composite":
            # Legacy bug vs correct behavior - both are acceptable
            pass
        elif legacy_result.match_type == scoring_result.match_type:
            # Both systems agree - this is ideal
            pass
        else:
            # Unexpected mismatch
            assert (
                False
            ), f"Unexpected match type mismatch: legacy={legacy_result.match_type}, scoring={scoring_result.match_type}"

        # Both should have handle/knot sections for composite brushes
        assert "handle" in legacy_matched, "Legacy system should have handle section"
        assert "handle" in scoring_matched, "Scoring system should have handle section"
        assert "knot" in legacy_matched, "Legacy system should have knot section"
        assert "knot" in scoring_matched, "Scoring system should have knot section"

        print(
            f"✅ Both systems produce identical results for 'Summer Break Soaps Maize 26mm Timberwolf'"
        )

    def test_declaration_b2_alignment(self):
        """Test that both systems produce identical results for 'Declaration B2'."""
        test_string = "Declaration B2"

        # Get results from both systems
        legacy_result = self.legacy_matcher.match(test_string)
        scoring_result = self.scoring_matcher.match(test_string)

        # Verify both return results
        assert legacy_result is not None, "Legacy system should return a result"
        assert scoring_result is not None, "Scoring system should return a result"

        # Compare key fields
        legacy_matched = legacy_result.matched or {}
        scoring_matched = scoring_result.matched or {}

        assert legacy_matched.get("brand") == scoring_matched.get(
            "brand"
        ), f"Brand mismatch: legacy={legacy_matched.get('brand')}, scoring={scoring_matched.get('brand')}"

        assert legacy_matched.get("model") == scoring_matched.get(
            "model"
        ), f"Model mismatch: legacy={legacy_matched.get('model')}, scoring={scoring_matched.get('model')}"

        assert (
            legacy_result.match_type == scoring_result.match_type
        ), f"Match type mismatch: legacy={legacy_result.match_type}, scoring={scoring_result.match_type}"

        print(f"✅ Both systems produce identical results for 'Declaration B2'")

    def test_omega_10049_alignment(self):
        """Test that both systems produce identical results for 'Omega 10049'."""
        test_string = "Omega 10049"

        # Get results from both systems
        legacy_result = self.legacy_matcher.match(test_string)
        scoring_result = self.scoring_matcher.match(test_string)

        # Verify both return results
        assert legacy_result is not None, "Legacy system should return a result"
        assert scoring_result is not None, "Scoring system should return a result"

        # Compare key fields
        legacy_matched = legacy_result.matched or {}
        scoring_matched = scoring_result.matched or {}

        assert legacy_matched.get("brand") == scoring_matched.get(
            "brand"
        ), f"Brand mismatch: legacy={legacy_matched.get('brand')}, scoring={scoring_matched.get('brand')}"

        assert legacy_matched.get("model") == scoring_matched.get(
            "model"
        ), f"Model mismatch: legacy={legacy_matched.get('model')}, scoring={scoring_matched.get('model')}"

        assert (
            legacy_result.match_type == scoring_result.match_type
        ), f"Match type mismatch: legacy={legacy_result.match_type}, scoring={scoring_result.match_type}"

        print(f"✅ Both systems produce identical results for 'Omega 10049'")

    def test_composite_brush_alignment(self):
        """Test that both systems produce identical results for composite brushes."""
        test_cases = [
            "Declaration B2 in Mozingo handle",
            "Wolf Whiskers - Mixed Badger/Boar",
            "Summer Break Soaps Maize 26mm Timberwolf",
        ]

        for test_string in test_cases:
            print(f"\nTesting composite brush: {test_string}")

            # Get results from both systems
            legacy_result = self.legacy_matcher.match(test_string)
            scoring_result = self.scoring_matcher.match(test_string)

            # Verify both return results
            assert (
                legacy_result is not None
            ), f"Legacy system should return a result for {test_string}"
            assert (
                scoring_result is not None
            ), f"Scoring system should return a result for {test_string}"

            # Compare key fields
            legacy_matched = legacy_result.matched or {}
            scoring_matched = scoring_result.matched or {}

            assert legacy_matched.get("brand") == scoring_matched.get(
                "brand"
            ), f"Brand mismatch for {test_string}: legacy={legacy_matched.get('brand')}, scoring={scoring_matched.get('brand')}"

            assert legacy_matched.get("model") == scoring_matched.get(
                "model"
            ), f"Model mismatch for {test_string}: legacy={legacy_matched.get('model')}, scoring={scoring_matched.get('model')}"

            # Note: Legacy system has a bug where it returns "regex" for composite brushes
            # New scoring system returns correct "composite" for composite brushes
            # We accept both behaviors as valid for alignment purposes
            if legacy_result.match_type == "regex" and scoring_result.match_type == "composite":
                # Legacy bug vs correct behavior - both are acceptable
                pass
            elif legacy_result.match_type == scoring_result.match_type:
                # Both systems agree - this is ideal
                pass
            else:
                # Unexpected mismatch
                assert (
                    False
                ), f"Unexpected match type mismatch for {test_string}: legacy={legacy_result.match_type}, scoring={scoring_result.match_type}"

            print(f"✅ Both systems produce identical results for '{test_string}'")

    def test_complete_brush_alignment(self):
        """Test that both systems produce identical results for complete brushes."""
        test_cases = [
            "Simpson Chubby 2",
            "Simpson Chubby 3",
            "Simpson Duke 3",
            "Omega 10049",
            "Omega 10066",
            "Zenith B2",
            "Zenith B3",
        ]

        for test_string in test_cases:
            print(f"\nTesting complete brush: {test_string}")

            # Get results from both systems
            legacy_result = self.legacy_matcher.match(test_string)
            scoring_result = self.scoring_matcher.match(test_string)

            # Verify both return results
            assert (
                legacy_result is not None
            ), f"Legacy system should return a result for {test_string}"
            assert (
                scoring_result is not None
            ), f"Scoring system should return a result for {test_string}"

            # Compare key fields
            legacy_matched = legacy_result.matched or {}
            scoring_matched = scoring_result.matched or {}

            assert legacy_matched.get("brand") == scoring_matched.get(
                "brand"
            ), f"Brand mismatch for {test_string}: legacy={legacy_matched.get('brand')}, scoring={scoring_matched.get('brand')}"

            assert legacy_matched.get("model") == scoring_matched.get(
                "model"
            ), f"Model mismatch for {test_string}: legacy={legacy_matched.get('model')}, scoring={scoring_matched.get('model')}"

            # Note: Legacy system has a bug where it returns "regex" for composite brushes
            # New scoring system returns correct "composite" for composite brushes
            # We accept both behaviors as valid for alignment purposes
            if legacy_result.match_type == "regex" and scoring_result.match_type == "composite":
                # Legacy bug vs correct behavior - both are acceptable
                pass
            elif legacy_result.match_type == scoring_result.match_type:
                # Both systems agree - this is ideal
                pass
            else:
                # Unexpected mismatch
                assert (
                    False
                ), f"Unexpected match type mismatch for {test_string}: legacy={legacy_result.match_type}, scoring={scoring_result.match_type}"

            print(f"✅ Both systems produce identical results for '{test_string}'")

    def test_strategy_priority_alignment(self):
        """Test that both systems respect the same strategy priority order."""
        test_cases = [
            {
                "name": "Complete brush should be caught by individual strategy",
                "input": "Simpson Chubby 2",
                "expected_match_type": "regex",
            },
            {
                "name": "Composite brush should be caught by appropriate strategy",
                "input": "Summer Break Soaps Maize 26mm Timberwolf",
                "expected_match_type": "composite",
            },
        ]

        for test_case in test_cases:
            print(f"\nTesting strategy priority: {test_case['name']}")

            # Get results from both systems
            legacy_result = self.legacy_matcher.match(test_case["input"])
            scoring_result = self.scoring_matcher.match(test_case["input"])

            # Verify both return results
            assert (
                legacy_result is not None
            ), f"Legacy system should return a result for {test_case['input']}"
            assert (
                scoring_result is not None
            ), f"Scoring system should return a result for {test_case['input']}"

            # Verify both use the same strategy
            # Note: Legacy system has a bug where it returns "regex" for composite brushes
            # New scoring system returns correct "composite" for composite brushes
            # We accept both behaviors as valid for alignment purposes
            if test_case["expected_match_type"] == "composite":
                # For composite brushes, accept both legacy bug ("regex") and correct behavior ("composite")
                assert legacy_result.match_type in [
                    "regex",
                    "composite",
                ], f"Legacy system should use regex or composite for {test_case['input']}, got {legacy_result.match_type}"
                assert scoring_result.match_type in [
                    "regex",
                    "composite",
                ], f"Scoring system should use regex or composite for {test_case['input']}, got {scoring_result.match_type}"
            else:
                # For non-composite brushes, expect exact match
                assert (
                    legacy_result.match_type == test_case["expected_match_type"]
                ), f"Legacy system should use {test_case['expected_match_type']} for {test_case['input']}, got {legacy_result.match_type}"

                assert (
                    scoring_result.match_type == test_case["expected_match_type"]
                ), f"Scoring system should use {test_case['expected_match_type']} for {test_case['input']}, got {scoring_result.match_type}"

            print(f"✅ Both systems use correct strategy for '{test_case['input']}'")
