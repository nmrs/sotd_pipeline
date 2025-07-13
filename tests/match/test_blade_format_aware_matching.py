"""Tests for format-aware blade matching algorithm."""

import pytest
import yaml

from sotd.match.blade_matcher import BladeMatcher


class TestFormatAwareCorrectMatchLookup:
    """Test the format-aware correct match lookup algorithm."""

    @pytest.fixture(scope="class")
    def sample_correct_matches(self):
        """Sample correct matches data for testing format-aware lookup."""
        return {
            "blade": {
                "DE": {
                    "Personna": {"Lab Blue": ["Accuforge"]},
                    "Astra": {"Superior Platinum (Green)": ["Astra"]},
                    "Feather": {"DE": ["Feather"]},
                },
                "GEM": {"Personna": {"GEM PTFE": ["Accuforge"]}},
                "AC": {"Feather": {"Pro": ["Feather"]}},
            }
        }

    @pytest.fixture(scope="class")
    def sample_catalog(self):
        """Sample catalog data with format information for testing."""
        return {
            "DE": {
                "Personna": {"Lab Blue": {"patterns": ["accuforge.*lab.*blue"]}},
                "Astra": {"Superior Platinum (Green)": {"patterns": ["astra"]}},
                "Feather": {"DE": {"patterns": ["feather"]}},
            },
            "GEM": {"Personna": {"GEM PTFE": {"patterns": ["accuforge.*ptfe"]}}},
            "AC": {"Feather": {"Pro": {"patterns": ["feather.*pro"]}}},
        }

    @pytest.fixture(scope="class")
    def test_matcher(self, sample_correct_matches, sample_catalog, tmp_path_factory):
        """Create a shared BladeMatcher instance for all tests."""
        tmp_path = tmp_path_factory.mktemp("blade_tests")

        # Create temporary files once
        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "blades.yaml"

        with open(correct_matches_file, "w") as f:
            yaml.dump(sample_correct_matches, f)

        with open(catalog_file, "w") as f:
            yaml.dump(sample_catalog, f)

        # Create matcher once and reuse
        return BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

    def test_format_specific_match_found_gem_razor(self, test_matcher):
        """Test that GEM razor with 'Accuforge' returns GEM PTFE match."""
        result = test_matcher.match_with_context("Accuforge", "GEM")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Personna"
        assert result["matched"]["model"] == "GEM PTFE"
        assert result["matched"]["format"] == "GEM"
        assert result["match_type"] == "exact"

    def test_format_specific_match_found_de_razor(self, test_matcher):
        """Test that DE razor with 'Accuforge' returns Lab Blue match."""
        result = test_matcher.match_with_context("Accuforge", "DE")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Personna"
        assert result["matched"]["model"] == "Lab Blue"
        assert result["matched"]["format"] == "DE"
        assert result["match_type"] == "exact"

    def test_single_match_exists(self, test_matcher):
        """Test that 'Astra' with DE razor returns Astra match (no format ambiguity)."""
        result = test_matcher.match_with_context("Astra", "DE")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Astra"
        assert result["matched"]["model"] == "Superior Platinum (Green)"
        assert result["match_type"] == "exact"

    def test_no_correct_match(self, test_matcher):
        """Test that 'Unknown Blade' with any razor returns None."""
        result = test_matcher.match_with_context("Unknown Blade", "DE")

        assert result["matched"] is None
        assert result["match_type"] is None

    def test_multiple_format_matches_de_razor(self, test_matcher):
        """Test that 'Feather' with DE razor returns DE Feather match."""
        result = test_matcher.match_with_context("Feather", "DE")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Feather"
        assert result["matched"]["model"] == "DE"
        assert result["matched"]["format"] == "DE"
        assert result["match_type"] == "exact"

    def test_multiple_format_matches_ac_razor(self, test_matcher):
        """Test that 'Feather' with AC razor returns AC Feather match."""
        result = test_matcher.match_with_context("Feather", "AC")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Feather"
        assert result["matched"]["model"] == "Pro"
        assert result["matched"]["format"] == "AC"
        assert result["match_type"] == "exact"

    def test_case_insensitive_matching(self, test_matcher):
        """Test that case variations return the same matches."""
        # Test exact case match (should work)
        result1 = test_matcher.match_with_context("Accuforge", "DE")
        assert result1["matched"] is not None
        assert result1["matched"]["brand"] == "Personna"
        assert result1["matched"]["model"] == "Lab Blue"

        # Test different case variations (should match due to case-insensitive fallback)
        result2 = test_matcher.match_with_context("ACCUFORGE", "DE")
        result3 = test_matcher.match_with_context("accuforge", "DE")

        # These should match because the implementation does case-insensitive fallback
        assert result2["matched"] is not None
        assert result2["matched"]["brand"] == "Personna"
        assert result2["matched"]["model"] == "Lab Blue"
        assert result3["matched"] is not None
        assert result3["matched"]["brand"] == "Personna"
        assert result3["matched"]["model"] == "Lab Blue"

    def test_no_match_when_format_not_found(self, test_matcher):
        """Test that no match is returned when the target format has no entries."""
        # Test with a razor format that has no Accuforge entries
        result = test_matcher.match_with_context("Accuforge", "STRAIGHT")

        # Should return no match since STRAIGHT format has no Accuforge entries
        assert result["matched"] is None
        assert result["match_type"] is None

    def test_half_de_fallback_to_de(self, test_matcher):
        """Test that HALF DE razors can use DE blades as fallback."""
        # Test HALF DE razor with Astra (which only has DE format)
        result = test_matcher.match_with_context("Astra", "SHAVETTE (HALF DE)")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Astra"
        assert result["matched"]["model"] == "Superior Platinum (Green)"
        assert result["match_type"] == "exact"
