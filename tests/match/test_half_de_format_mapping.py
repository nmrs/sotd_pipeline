"""Test Half DE format mapping and matching behavior."""

from sotd.match.blade_matcher import BladeMatcher


class TestHalfDEFormatMapping:
    """Test Half DE format mapping and matching behavior."""

    def test_format_mapping(self):
        """Test that Half DE razor formats map to HALF DE blade format."""
        matcher = BladeMatcher()

        # Test various Half DE razor formats
        test_cases = [
            ("Half DE", "HALF DE"),
            ("Half DE (multi-blade)", "HALF DE"),
            ("SHAVETTE (HALF DE)", "HALF DE"),
            ("half de", "HALF DE"),  # Case insensitive
            ("HALF DE", "HALF DE"),  # Already normalized
        ]

        for razor_format, expected_blade_format in test_cases:
            result = matcher._get_target_blade_format(razor_format)
            assert (
                result == expected_blade_format
            ), f"Expected {razor_format} -> {expected_blade_format}, got {result}"

    def test_half_de_priority_matching(self, tmp_path):
        """Test that Half DE razors prioritize Half DE blades over DE blades."""
        # Create test catalog with both Half DE and DE blades
        catalog_data = {
            "HALF DE": {
                "Gillette": {
                    "Perma-Sharp SE": {"patterns": ["perma.*sharp.*se"], "format": "HALF DE"}
                }
            },
            "DE": {"Gillette": {"Perma-Sharp": {"patterns": ["perma.*sharp"], "format": "DE"}}},
        }

        # Create test correct matches
        correct_matches_data = {
            "blade": {
                "HALF DE": {"Gillette": {"Perma-Sharp SE": ["Perma-Sharp SE"]}},
                "DE": {"Gillette": {"Perma-Sharp": ["Perma-Sharp"]}},
            }
        }

        # Write test files
        catalog_file = tmp_path / "blades.yaml"
        correct_matches_file = tmp_path / "correct_matches.yaml"

        import yaml

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Create matcher with test files
        matcher = BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

        # Test that Half DE razor prioritizes Half DE blade
        result = matcher.match_with_context("Perma-Sharp SE", "Half DE")
        assert result.matched is not None
        assert result.matched["format"] == "HALF DE"
        assert result.matched["model"] == "Perma-Sharp SE"

        # Test that Half DE razor falls back to DE blade when no Half DE match
        result = matcher.match_with_context("Perma-Sharp", "Half DE")
        assert result.matched is not None
        assert result.matched["format"] == "DE"
        assert result.matched["model"] == "Perma-Sharp"

    def test_de_razor_half_de_fallback(self, tmp_path):
        """Test that DE razors can fall back to Half DE blades."""
        # Create test catalog with Half DE blades
        catalog_data = {
            "HALF DE": {
                "Gillette": {
                    "Perma-Sharp SE": {"patterns": ["perma.*sharp.*se"], "format": "HALF DE"}
                }
            },
            "DE": {"Gillette": {"Perma-Sharp": {"patterns": ["perma.*sharp"], "format": "DE"}}},
        }

        # Create test correct matches - use a blade that only exists in Half DE
        correct_matches_data = {
            "blade": {
                "HALF DE": {"Gillette": {"Perma-Sharp SE": ["Half DE Only Blade"]}},
                "DE": {"Gillette": {"Perma-Sharp": ["Perma-Sharp"]}},
            }
        }

        # Write test files
        catalog_file = tmp_path / "blades.yaml"
        correct_matches_file = tmp_path / "correct_matches.yaml"

        import yaml

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Create matcher with test files
        matcher = BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

        # Test that DE razor can fall back to Half DE blade when no DE match exists
        result = matcher.match_with_context("Half DE Only Blade", "DE")
        assert result.matched is not None
        assert result.matched["format"] == "HALF DE"
        assert result.matched["model"] == "Perma-Sharp SE"

    def test_shavette_half_de_mapping(self, tmp_path):
        """Test that Shavette (Half DE) razors map correctly."""
        # Create test catalog
        catalog_data = {
            "HALF DE": {
                "Gillette": {
                    "Perma-Sharp SE": {"patterns": ["perma.*sharp.*se"], "format": "HALF DE"}
                }
            }
        }

        # Create test correct matches
        correct_matches_data = {
            "blade": {"HALF DE": {"Gillette": {"Perma-Sharp SE": ["Perma-Sharp SE"]}}}
        }

        # Write test files
        catalog_file = tmp_path / "blades.yaml"
        correct_matches_file = tmp_path / "correct_matches.yaml"

        import yaml

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Create matcher with test files
        matcher = BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

        # Test Shavette (Half DE) format mapping
        result = matcher.match_with_context("Perma-Sharp SE", "SHAVETTE (HALF DE)")
        assert result.matched is not None
        assert result.matched["format"] == "HALF DE"
        assert result.matched["model"] == "Perma-Sharp SE"

    def test_multi_blade_format_mapping(self, tmp_path):
        """Test that Half DE (multi-blade) razors map correctly."""
        # Create test catalog
        catalog_data = {
            "HALF DE": {
                "Gillette": {
                    "Perma-Sharp SE": {"patterns": ["perma.*sharp.*se"], "format": "HALF DE"}
                }
            }
        }

        # Create test correct matches
        correct_matches_data = {
            "blade": {"HALF DE": {"Gillette": {"Perma-Sharp SE": ["Perma-Sharp SE"]}}}
        }

        # Write test files
        catalog_file = tmp_path / "blades.yaml"
        correct_matches_file = tmp_path / "correct_matches.yaml"

        import yaml

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Create matcher with test files
        matcher = BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

        # Test Half DE (multi-blade) format mapping
        result = matcher.match_with_context("Perma-Sharp SE", "Half DE (multi-blade)")
        assert result.matched is not None
        assert result.matched["format"] == "HALF DE"
        assert result.matched["model"] == "Perma-Sharp SE"

    def test_no_half_de_fallback_when_half_de_exists(self, tmp_path):
        """Test that Half DE razors don't fall back to DE when Half DE match exists."""
        # Create test catalog with both formats
        catalog_data = {
            "HALF DE": {
                "Gillette": {"Perma-Sharp SE": {"patterns": ["perma.*sharp"], "format": "HALF DE"}}
            },
            "DE": {"Gillette": {"Perma-Sharp": {"patterns": ["perma.*sharp"], "format": "DE"}}},
        }

        # Create test correct matches
        correct_matches_data = {
            "blade": {
                "HALF DE": {"Gillette": {"Perma-Sharp SE": ["Perma-Sharp"]}},
                "DE": {"Gillette": {"Perma-Sharp": ["Perma-Sharp"]}},
            }
        }

        # Write test files
        catalog_file = tmp_path / "blades.yaml"
        correct_matches_file = tmp_path / "correct_matches.yaml"

        import yaml

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Create matcher with test files
        matcher = BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

        # Test that Half DE razor prioritizes Half DE blade over DE
        result = matcher.match_with_context("Perma-Sharp", "Half DE")
        assert result.matched is not None
        assert result.matched["format"] == "HALF DE"
        assert result.matched["model"] == "Perma-Sharp SE"
