"""Tests for BaseMatcher optimization features."""

from pathlib import Path

from sotd.match.base_matcher import BaseMatcher


class TestBaseMatcherOptimization:
    """Test the optimization features of BaseMatcher."""

    def test_lazy_loading_correct_matches_lookup(self):
        """Test that correct matches lookup is lazy loaded."""
        # Create a mock catalog path
        catalog_path = Path("data/razors.yaml")

        # Create BaseMatcher instance
        matcher = BaseMatcher(catalog_path, "razor")

        # Initially, the lookup should be None
        assert matcher._correct_matches_lookup is None

        # Access the lookup (should trigger lazy loading)
        lookup = matcher._get_correct_matches_lookup()

        # Now the lookup should be populated
        assert matcher._correct_matches_lookup is not None
        assert isinstance(lookup, dict)

    def test_lazy_loading_catalog_patterns(self):
        """Test that catalog patterns are lazy loaded."""
        # Create a mock catalog path
        catalog_path = Path("data/razors.yaml")

        # Create BaseMatcher instance
        matcher = BaseMatcher(catalog_path, "razor")

        # Initially, the patterns should be None
        assert matcher._catalog_patterns is None

        # Access the patterns (should trigger lazy loading)
        patterns = matcher._get_catalog_patterns()

        # Now the patterns should be populated
        assert matcher._catalog_patterns is not None
        assert isinstance(patterns, list)

    def test_compiled_patterns_caching(self):
        """Test that compiled patterns are cached."""
        # Create a mock catalog path
        catalog_path = Path("data/razors.yaml")

        # Create BaseMatcher instance
        matcher = BaseMatcher(catalog_path, "razor")

        # Initially, no compiled patterns
        assert len(matcher._compiled_patterns) == 0

        # Get a compiled pattern
        pattern1 = matcher._get_compiled_pattern("test.*pattern")
        assert pattern1 is not None

        # Should be cached
        assert len(matcher._compiled_patterns) == 1
        assert "test.*pattern" in matcher._compiled_patterns

        # Getting the same pattern again should return the cached version
        pattern2 = matcher._get_compiled_pattern("test.*pattern")
        assert pattern1 is pattern2  # Same object reference

        # Invalid pattern should return None and not be cached
        invalid_pattern = matcher._get_compiled_pattern("invalid[pattern")
        assert invalid_pattern is None
        assert "invalid[pattern" not in matcher._compiled_patterns

    def test_clear_caches(self):
        """Test that clear_caches() resets all caches."""
        # Create a mock catalog path
        catalog_path = Path("data/razors.yaml")

        # Create BaseMatcher instance
        matcher = BaseMatcher(catalog_path, "razor")

        # Populate caches
        matcher._get_correct_matches_lookup()
        matcher._get_catalog_patterns()
        matcher._get_compiled_pattern("test.*pattern")

        # Verify caches are populated
        assert matcher._correct_matches_lookup is not None
        assert matcher._catalog_patterns is not None
        assert len(matcher._compiled_patterns) > 0

        # Clear caches
        matcher.clear_caches()

        # Verify caches are cleared
        assert matcher._correct_matches_lookup is None
        assert matcher._catalog_patterns is None
        assert len(matcher._compiled_patterns) == 0

    def test_o1_lookup_performance(self):
        """Test that correct matches lookup is O(1) instead of O(n×m×p)."""
        # Create a mock catalog path
        catalog_path = Path("data/razors.yaml")

        # Create BaseMatcher instance
        matcher = BaseMatcher(catalog_path, "razor")

        # Mock the correct_matches data to simulate a large dataset
        matcher.correct_matches = {
            "Brand1": {
                "Model1": ["string1", "string2", "string3"],
                "Model2": ["string4", "string5"],
            },
            "Brand2": {
                "Model3": ["string6", "string7", "string8", "string9"],
                "Model4": ["string10"],
            },
        }

        # Mock the catalog data
        matcher.catalog = {
            "Brand1": {
                "Model1": {"format": "DE", "grind": "full_hollow"},
                "Model2": {"format": "DE", "grind": "half_hollow"},
            },
            "Brand2": {
                "Model3": {"format": "DE", "grind": "quarter_hollow"},
                "Model4": {"format": "DE", "grind": "wedge"},
            },
        }

        # Build the lookup (this should be the one-time O(n×m×p) cost)
        lookup = matcher._get_correct_matches_lookup()

        # Verify lookup structure
        assert "string1" in lookup
        assert "string10" in lookup
        assert lookup["string1"]["brand"] == "Brand1"
        assert lookup["string1"]["model"] == "Model1"
        assert lookup["string1"]["format"] == "DE"
        assert lookup["string1"]["grind"] == "full_hollow"

        # Test O(1) lookup performance
        # These should be fast dictionary lookups, not nested loops
        result1 = matcher._check_correct_matches("string1")
        result2 = matcher._check_correct_matches("string10")
        result3 = matcher._check_correct_matches("nonexistent")

        assert result1 is not None
        assert result1["brand"] == "Brand1"
        assert result1["model"] == "Model1"

        assert result2 is not None
        assert result2["brand"] == "Brand2"
        assert result2["model"] == "Model4"

        assert result3 is None

    def test_soap_field_pattern_extraction(self):
        """Test pattern extraction for soap field type."""
        # Create a mock catalog path
        catalog_path = Path("data/soaps.yaml")

        # Create BaseMatcher instance for soap
        matcher = BaseMatcher(catalog_path, "soap")

        # Mock soap catalog data structure
        matcher.catalog = {
            "Maker1": {
                "scents": {
                    "Scent1": {
                        "patterns": ["pattern1", "pattern2"],
                    },
                    "Scent2": {
                        "patterns": ["pattern3"],
                    },
                },
            },
            "Maker2": {
                "scents": {
                    "Scent3": {
                        "patterns": ["pattern4", "pattern5", "pattern6"],
                    },
                },
            },
        }

        # Extract patterns
        patterns = matcher._extract_patterns_from_catalog()

        # Verify patterns are extracted correctly
        assert len(patterns) == 6

        # Check structure
        pattern_dict = {p["pattern"]: p for p in patterns}
        assert "pattern1" in pattern_dict
        assert pattern_dict["pattern1"]["maker"] == "Maker1"
        assert pattern_dict["pattern1"]["scent"] == "Scent1"

        assert "pattern4" in pattern_dict
        assert pattern_dict["pattern4"]["maker"] == "Maker2"
        assert pattern_dict["pattern4"]["scent"] == "Scent3"

    def test_razor_field_pattern_extraction(self):
        """Test pattern extraction for razor field type."""
        # Create a mock catalog path
        catalog_path = Path("data/razors.yaml")

        # Create BaseMatcher instance for razor
        matcher = BaseMatcher(catalog_path, "razor")

        # Mock razor catalog data structure
        matcher.catalog = {
            "Brand1": {
                "Model1": {
                    "patterns": ["pattern1", "pattern2"],
                    "format": "DE",
                },
                "Model2": {
                    "patterns": ["pattern3"],
                    "format": "DE",
                },
            },
            "Brand2": {
                "Model3": {
                    "patterns": ["pattern4", "pattern5"],
                    "format": "DE",
                },
            },
        }

        # Extract patterns
        patterns = matcher._extract_patterns_from_catalog()

        # Verify patterns are extracted correctly
        assert len(patterns) == 5

        # Check structure
        pattern_dict = {p["pattern"]: p for p in patterns}
        assert "pattern1" in pattern_dict
        assert pattern_dict["pattern1"]["brand"] == "Brand1"
        assert pattern_dict["pattern1"]["model"] == "Model1"

        assert "pattern4" in pattern_dict
        assert pattern_dict["pattern4"]["brand"] == "Brand2"
        assert pattern_dict["pattern4"]["model"] == "Model3"
