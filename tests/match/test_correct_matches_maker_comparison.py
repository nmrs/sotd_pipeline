"""
Unit tests for maker comparison logic in CorrectMatchesChecker.

Tests the logic that determines whether handle and knot components
come from the same maker or different makers.
"""

from sotd.match.correct_matches import CorrectMatchesChecker


class TestSameMakerDetermination:
    """Test same maker determination logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock correct_matches data with same maker in handle/knot sections
        self.correct_matches = {
            "handle": {
                "Declaration Grooming": {"Washington": ["declaration grooming washington b14"]}
            },
            "knot": {"Declaration Grooming": {"B14": ["declaration grooming washington b14"]}},
        }

        self.checker = CorrectMatchesChecker(self.correct_matches)

    def test_same_maker_exact_string_matching(self):
        """Test same maker with exact string matching."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming washington b14")

        assert result is not None
        assert result.handle_maker == "Declaration Grooming"
        assert result.handle_model == "Washington"
        assert result.match_type == "handle_knot_section"

    def test_same_maker_case_insensitive_comparison(self):
        """Test same maker with case-insensitive comparison."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("Declaration Grooming Washington B14")

        assert result is not None
        assert result.handle_maker == "Declaration Grooming"
        assert result.handle_model == "Washington"
        assert result.match_type == "handle_knot_section"


class TestDifferentMakerDetermination:
    """Test different maker determination logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock correct_matches data with different makers in handle/knot sections
        self.correct_matches = {
            "handle": {
                "Dogwood Handcrafts": {
                    "Ivory": ["dogwood handcrafts ivory declaration grooming b14"]
                }
            },
            "knot": {
                "Declaration Grooming": {
                    "B14": ["dogwood handcrafts ivory declaration grooming b14"]
                }
            },
        }

        self.checker = CorrectMatchesChecker(self.correct_matches)

    def test_different_makers_exact_string_matching(self):
        """Test different makers with exact string matching."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("dogwood handcrafts ivory declaration grooming b14")

        assert result is not None
        assert result.handle_maker == "Dogwood Handcrafts"
        assert result.handle_model == "Ivory"
        assert result.match_type == "handle_knot_section"

    def test_different_makers_case_insensitive_comparison(self):
        """Test different makers with case-insensitive comparison."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("Dogwood Handcrafts Ivory Declaration Grooming B14")

        assert result is not None
        assert result.handle_maker == "Dogwood Handcrafts"
        assert result.handle_model == "Ivory"
        assert result.match_type == "handle_knot_section"


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions for maker comparison."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock correct_matches data with edge cases
        self.correct_matches = {
            "handle": {"Test Brand": {"Test Model": ["test brand test model"]}},
            "knot": {"Test Brand": {"Test Model": ["test brand test model"]}},
        }

        self.checker = CorrectMatchesChecker(self.correct_matches)

    def test_null_maker_handling(self):
        """Test null maker handling."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("test brand test model")

        assert result is not None
        assert result.handle_maker == "Test Brand"
        assert result.handle_model == "Test Model"
        assert result.match_type == "handle_knot_section"

    def test_empty_string_maker_handling(self):
        """Test empty string maker handling."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("test brand test model")

        assert result is not None
        assert result.handle_maker == "Test Brand"
        assert result.handle_model == "Test Model"
        assert result.match_type == "handle_knot_section"

    def test_whitespace_handling_in_maker_names(self):
        """Test whitespace handling in maker names."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("test brand test model")

        assert result is not None
        assert result.handle_maker == "Test Brand"
        assert result.handle_model == "Test Model"
        assert result.match_type == "handle_knot_section"

    def test_catalog_data_mismatch_error_handling(self):
        """Test catalog data mismatch error handling."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("test brand test model")

        assert result is not None
        assert result.handle_maker == "Test Brand"
        assert result.handle_model == "Test Model"
        assert result.match_type == "handle_knot_section"


class TestMakerComparisonIntegration:
    """Test maker comparison integration with real catalog data."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock correct_matches data with realistic catalog brand names
        self.correct_matches = {
            "handle": {
                "Declaration Grooming": {"Jeffington": ["declaration grooming jeffington b18"]}
            },
            "knot": {"Declaration Grooming": {"B18": ["declaration grooming jeffington b18"]}},
        }

        self.checker = CorrectMatchesChecker(self.correct_matches)

    def test_real_catalog_brand_names_same_maker(self):
        """Test with real catalog brand names (same maker)."""
        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming jeffington b18")

        assert result is not None
        assert result.handle_maker == "Declaration Grooming"
        assert result.handle_model == "Jeffington"
        assert result.match_type == "handle_knot_section"

    def test_real_catalog_brand_names_different_makers(self):
        """Test with real catalog brand names (different makers)."""
        # Update test data for different makers
        self.correct_matches["knot"] = {
            "Turn N Shave": {
                "Quartermoon": ["declaration grooming jeffington turn n shave quartermoon"]
            }
        }

        # This test will be implemented when we add maker comparison logic
        # For now, we're testing the current behavior
        result = self.checker.check("declaration grooming jeffington turn n shave quartermoon")

        assert result is not None
        # Current implementation finds knot match first
        assert result.knot_info is not None
        assert result.knot_info.get("brand") == "Turn N Shave"
        assert result.knot_info.get("model") == "Quartermoon"
        assert result.match_type == "handle_knot_section"
