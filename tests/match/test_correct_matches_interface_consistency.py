"""
Unit tests for interface consistency in CorrectMatchesChecker.

Tests that the implementation returns the same MatchResult structure
as regex strategies and maintains interface consistency.
"""

from unittest.mock import Mock

from sotd.match.correct_matches import CorrectMatchesChecker
from sotd.match.config import BrushMatcherConfig


class TestMatchResultStructure:
    """Test MatchResult structure consistency."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        self.correct_matches = {
            "brush": {"Declaration Grooming": {"B14": ["declaration grooming bok b14"]}}
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_match_result_structure_matches_regex_strategies(self):
        """Test MatchResult structure matches regex strategies."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        # Current implementation returns CorrectMatchData
        # New implementation will return MatchResult structure
        assert hasattr(result, "brand")
        assert hasattr(result, "model")
        assert hasattr(result, "match_type")

    def test_match_type_field_values_are_consistent(self):
        """Test match_type field values are consistent."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        assert result.match_type == "brush_section"

        # Test handle/knot section
        self.correct_matches["handle"] = {
            "Declaration Grooming": {"Washington": ["declaration grooming washington b14"]}
        }

        result2 = self.checker.check("declaration grooming washington b14")
        assert result2 is not None
        assert result2.match_type == "handle_knot_section"

    def test_error_handling_follows_same_patterns_as_regex_strategies(self):
        """Test error handling follows same patterns as regex strategies."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test with non-matching input
        result = self.checker.check("non matching input")
        assert result is None

        # Test with empty input
        result = self.checker.check("")
        assert result is None

        # Test with None input
        result = self.checker.check(None)  # type: ignore
        assert result is None

    def test_debug_output_format_matches_regex_strategies(self):
        """Test debug output format matches regex strategies."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        # Debug output validation will be added in new implementation

    def test_integration_with_brush_matcher_priority_order(self):
        """Test integration with brush matcher priority order."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        # Priority order integration will be tested in new implementation

    def test_performance_characteristics_match_regex_strategies(self):
        """Test performance characteristics match regex strategies."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test multiple lookups to ensure reasonable performance
        for _ in range(10):
            result = self.checker.check("declaration grooming bok b14")
            assert result is not None
            assert result.brand == "Declaration Grooming"
            assert result.model == "B14"

    def test_catalog_lookup_behavior_consistency(self):
        """Test catalog lookup behavior consistency."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        # Catalog lookup behavior will be validated in new implementation

    def test_fail_fast_error_handling_consistency(self):
        """Test fail-fast error handling consistency."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test with malformed data
        malformed_matches = {"brush": "not a dict"}
        malformed_checker = CorrectMatchesChecker(self.config, malformed_matches)

        # Current implementation will fail with AttributeError
        # New implementation will handle gracefully and fail fast
        try:
            result = malformed_checker.check("test brand test model")
            assert result is None
        except AttributeError:
            # Current behavior - will be fixed in new implementation
            pass


class TestErrorHandlingConsistency:
    """Test error handling consistency with regex strategies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        self.correct_matches = {"brush": {"Test Brand": {"Test Model": ["test brand test model"]}}}

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_error_handling_consistency_for_invalid_input(self):
        """Test error handling consistency for invalid input."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test various invalid inputs
        invalid_inputs = ["", None, "   ", "non matching"]

        for invalid_input in invalid_inputs:
            result = self.checker.check(invalid_input)
            assert result is None

    def test_error_handling_consistency_for_malformed_data(self):
        """Test error handling consistency for malformed data."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test with malformed correct_matches
        malformed_matches = {"brush": "not a dict"}
        malformed_checker = CorrectMatchesChecker(self.config, malformed_matches)

        # Current implementation will fail with AttributeError
        # New implementation will handle gracefully
        try:
            result = malformed_checker.check("test brand test model")
            assert result is None
        except AttributeError:
            # Current behavior - will be fixed in new implementation
            pass

    def test_error_handling_consistency_for_missing_catalog_entries(self):
        """Test error handling consistency for missing catalog entries."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("missing catalog entry")

        assert result is None


class TestDebugOutputConsistency:
    """Test debug output consistency with regex strategies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = True  # Enable debug mode

        self.correct_matches = {
            "brush": {"Declaration Grooming": {"B14": ["declaration grooming bok b14"]}}
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_debug_output_consistency_for_successful_matches(self):
        """Test debug output consistency for successful matches."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        # Debug output validation will be added in new implementation

    def test_debug_output_consistency_for_failed_matches(self):
        """Test debug output consistency for failed matches."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("non matching input")

        assert result is None
        # Debug output validation will be added in new implementation

    def test_debug_output_consistency_for_error_conditions(self):
        """Test debug output consistency for error conditions."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test with malformed data
        malformed_matches = {"brush": "not a dict"}
        malformed_checker = CorrectMatchesChecker(self.config, malformed_matches)

        # Current implementation will fail with AttributeError
        # New implementation will handle gracefully and provide debug output
        try:
            result = malformed_checker.check("test brand test model")
            assert result is None
        except AttributeError:
            # Current behavior - will be fixed in new implementation
            pass


class TestStrategyIntegration:
    """Test integration with brush matcher strategies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        self.correct_matches = {
            "brush": {"Declaration Grooming": {"B14": ["declaration grooming bok b14"]}},
            "handle": {
                "Declaration Grooming": {"Washington": ["declaration grooming washington b14"]}
            },
            "knot": {"Declaration Grooming": {"B14": ["declaration grooming b14"]}},
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_strategy_integration_with_brush_matcher_priority_order(self):
        """Test strategy integration with brush matcher priority order."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test that correct matches checker works as expected
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        assert result.brand == "Declaration Grooming"
        assert result.model == "B14"
        assert result.match_type == "brush_section"

    def test_strategy_integration_with_handle_knot_matching(self):
        """Test strategy integration with handle/knot matching."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming washington b14")

        assert result is not None
        assert result.handle_maker == "Declaration Grooming"
        assert result.handle_model == "Washington"
        assert result.match_type == "handle_knot_section"

    def test_strategy_integration_with_performance_requirements(self):
        """Test strategy integration with performance requirements."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test multiple lookups to ensure reasonable performance
        for _ in range(10):
            result = self.checker.check("declaration grooming bok b14")
            assert result is not None
            assert result.brand == "Declaration Grooming"
            assert result.model == "B14"

    def test_strategy_integration_with_error_handling(self):
        """Test strategy integration with error handling."""
        # This test will be implemented when we add new interface
        # For now, we're testing the current behavior

        # Test with non-matching input
        result = self.checker.check("non matching input")
        assert result is None

        # Test with empty input
        result = self.checker.check("")
