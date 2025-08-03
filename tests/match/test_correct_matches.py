"""
Tests for the CorrectMatchesChecker component.
"""

from sotd.match.config import BrushMatcherConfig
from sotd.match.correct_matches import CorrectMatchesChecker


class TestCorrectMatchesChecker:
    """Test the CorrectMatchesChecker component."""

    def setup_method(self):
        """Set up test data and configuration."""
        self.config = BrushMatcherConfig.create_default()

        # Test correct matches data
        self.test_correct_matches = {
            "brush": {
                "Test Brand": {"Test Model": ["test brush", "test brush model"]},
                "Another Brand": {"Another Model": ["another brush"]},
            },
            "handle": {
                "Test Handle Maker": {
                    "Test Handle": ["test handle w/ knot", "test handle with knot"]
                }
            },
            "knot": {
                "Test Knot Maker": {
                    "Test Knot": {
                        "fiber": "Badger",
                        "knot_size_mm": 26.0,
                        "strings": ["test handle w/ knot", "test handle with knot"],
                    }
                }
            },
        }

        self.checker = CorrectMatchesChecker(self.config, self.test_correct_matches)

    def test_check_brush_section_match(self):
        """Test that brush section matches work correctly."""
        result = self.checker.check("test brush")
        assert result is not None
        assert result.brand == "Test Brand"
        assert result.model == "Test Model"
        assert result.match_type == "brush_section"

    def test_check_brush_section_no_match(self):
        """Test that non-matching brush inputs return None."""
        result = self.checker.check("unknown brush")
        assert result is None

    def test_check_handle_knot_section_match(self):
        """Test that handle/knot section matches work correctly."""
        result = self.checker.check("test handle w/ knot")
        assert result is not None
        assert result.handle_maker == "Test Handle Maker"
        assert result.handle_model == "Test Handle"
        assert result.match_type == "handle_knot_section"
        assert result.knot_info is not None
        assert result.knot_info["brand"] == "Test Knot Maker"
        assert result.knot_info["model"] == "Test Knot"

    def test_check_handle_knot_section_no_match(self):
        """Test that non-matching handle/knot inputs return None."""
        result = self.checker.check("unknown handle w/ knot")
        assert result is None

    def test_check_empty_input(self):
        """Test that empty input returns None."""
        result = self.checker.check("")
        assert result is None

    def test_check_none_input(self):
        """Test that None input returns None."""
        result = self.checker.check(None)  # type: ignore
        assert result is None

    def test_check_empty_correct_matches(self):
        """Test that empty correct matches data returns None."""
        empty_checker = CorrectMatchesChecker(self.config, {})
        result = empty_checker.check("test brush")
        assert result is None

    def test_check_normalized_matching(self):
        """Test that normalization works correctly for matching."""
        # Test with different spacing (normalization preserves case)
        result = self.checker.check("test  brush")  # Extra spaces
        assert result is not None
        assert result.brand == "Test Brand"
        assert result.model == "Test Model"

    def test_check_multiple_brush_entries(self):
        """Test that multiple brush entries are checked correctly."""
        result = self.checker.check("another brush")
        assert result is not None
        assert result.brand == "Another Brand"
        assert result.model == "Another Model"

    def test_check_multiple_handle_entries(self):
        """Test that multiple handle entries are checked correctly."""
        result = self.checker.check("test handle with knot")
        assert result is not None
        assert result.handle_maker == "Test Handle Maker"
        assert result.handle_model == "Test Handle"

    def test_check_knot_info_structure(self):
        """Test that knot info has the correct structure."""
        result = self.checker.check("test handle w/ knot")
        assert result is not None
        knot_info = result.knot_info
        assert knot_info is not None
        assert knot_info["brand"] == "Test Knot Maker"
        assert knot_info["model"] == "Test Knot"
        assert knot_info["fiber"] == "Badger"
        assert knot_info["knot_size_mm"] == 26.0
        assert "strings" in knot_info

    def test_check_handle_only_no_knot_match(self):
        """Test handle section match when no corresponding knot is found."""
        # Create checker with handle but no matching knot
        handle_only_matches = {
            "handle": {"Test Handle Maker": {"Test Handle": ["handle only"]}},
            "knot": {},  # Empty knot section
        }
        checker = CorrectMatchesChecker(self.config, handle_only_matches)

        result = checker.check("handle only")
        assert result is not None
        assert result.handle_maker == "Test Handle Maker"
        assert result.handle_model == "Test Handle"
        assert result.knot_info is None

    def test_get_statistics(self):
        """Test that statistics are calculated correctly."""
        stats = self.checker.get_statistics()

        assert stats["total_brush_entries"] == 3  # 2 + 1
        assert stats["total_handle_entries"] == 2  # 2 handle entries
        assert stats["total_knot_entries"] == 2  # 2 knot strings
        assert stats["total_entries"] == 7  # 3 + 2 + 2
        assert stats["brands_in_brush_section"] == 2
        assert stats["handle_makers"] == 1
        assert stats["knot_makers"] == 1

    def test_get_statistics_empty_data(self):
        """Test statistics with empty correct matches data."""
        empty_checker = CorrectMatchesChecker(self.config, {})
        stats = empty_checker.get_statistics()

        assert stats["total_brush_entries"] == 0
        assert stats["total_handle_entries"] == 0
        assert stats["total_knot_entries"] == 0
        assert stats["total_entries"] == 0
        assert stats["brands_in_brush_section"] == 0
        assert stats["handle_makers"] == 0
        assert stats["knot_makers"] == 0

    def test_check_with_invalid_data_structure(self):
        """Test that invalid data structures are handled gracefully."""
        invalid_matches = {
            "brush": {
                "Test Brand": "not a dict",  # Invalid structure
                "Another Brand": {"Model": "not a list"},  # Invalid structure
            },
            "handle": {"Handle Maker": {"Handle": "not a list"}},  # Invalid structure
        }

        checker = CorrectMatchesChecker(self.config, invalid_matches)

        # Should not raise exceptions, just return None
        result = checker.check("test brush")
        assert result is None

        stats = checker.get_statistics()
        assert stats["total_brush_entries"] == 0
        assert stats["total_handle_entries"] == 0

    def test_check_priority_brush_first(self):
        """Test that brush section is checked before handle/knot section."""
        # Create data where the same string could match both sections
        priority_matches = {
            "brush": {"Brush Brand": {"Brush Model": ["test string"]}},
            "handle": {"Handle Maker": {"Handle Model": ["test string"]}},
            "knot": {"Knot Maker": {"Knot Model": {"fiber": "Badger", "strings": ["test string"]}}},
        }

        checker = CorrectMatchesChecker(self.config, priority_matches)
        result = checker.check("test string")

        # Should match brush section first (new priority order)
        assert result is not None
        assert result.match_type == "brush_section"
        assert result.brand == "Brush Brand"
        assert result.model == "Brush Model"
