"""Tests for HandleMatcher with unified MatchResult support."""

from sotd.match.handle_matcher import HandleMatcher
from sotd.match.types import MatchResult


class TestHandleMatcherUnifiedMatchResult:
    """Test HandleMatcher with unified MatchResult support."""

    def test_handle_matcher_returns_section_match_result(self, tmp_path):
        """Test that handle matcher returns MatchResult with section/priority."""
        # Create a simple handles.yaml file
        handles_yaml = """
artisan_handles:
  Elite:
    Zebra:
      patterns:
        - "elite.*zebra"
        - "zebra.*handle"
manufacturer_handles:
  Chisel & Hound:
    Jeffington:
      patterns:
        - "ch.*jeffington"
        - "jeffington.*handle"
other_handles:
  Generic:
    Standard:
      patterns:
        - "generic.*handle"
"""
        handles_file = tmp_path / "handles.yaml"
        handles_file.write_text(handles_yaml)

        matcher = HandleMatcher(handles_path=handles_file)
        result = matcher.match("Elite Zebra Handle")

        assert isinstance(result, MatchResult)
        assert result.section == "artisan_handles"  # Elite should be in artisan_handles
        assert result.priority == 1  # artisan_handles should have priority 1
        assert result.matched is not None
        assert result.matched["handle_maker"] == "Elite"
        assert result.matched["handle_model"] == "Zebra"
        assert result.has_section_info

    def test_handle_matcher_returns_manufacturer_section(self, tmp_path):
        """Test that manufacturer_handles strategy returns correct section/priority."""
        # Create a simple handles.yaml file
        handles_yaml = """
artisan_handles:
  Elite:
    Zebra:
      patterns:
        - "elite.*zebra"
manufacturer_handles:
  Chisel & Hound:
    Jeffington:
      patterns:
        - "ch.*jeffington"
        - "jeffington.*handle"
other_handles:
  Generic:
    Standard:
      patterns:
        - "generic.*handle"
"""
        handles_file = tmp_path / "handles.yaml"
        handles_file.write_text(handles_yaml)

        matcher = HandleMatcher(handles_path=handles_file)
        result = matcher.match("Chisel & Hound Jeffington")

        assert isinstance(result, MatchResult)
        assert result.section == "manufacturer_handles"  # Should be in manufacturer_handles
        assert result.priority == 2  # Should have priority 2 (second section)
        assert result.matched is not None
        assert result.matched["handle_maker"] == "Chisel & Hound"
        assert result.matched["handle_model"] == "Jeffington"
        assert result.has_section_info

    def test_handle_matcher_no_match_returns_none(self, tmp_path):
        """Test that no match returns None."""
        # Create a simple handles.yaml file
        handles_yaml = """
artisan_handles:
  Elite:
    Zebra:
      patterns:
        - "elite.*zebra"
"""
        handles_file = tmp_path / "handles.yaml"
        handles_file.write_text(handles_yaml)

        matcher = HandleMatcher(handles_path=handles_file)
        result = matcher.match("Unknown Handle")

        assert result is None

    def test_handle_matcher_backward_compatibility(self, tmp_path):
        """Test that match_handle_maker method still works for backward compatibility."""
        # Create a simple handles.yaml file
        handles_yaml = """
artisan_handles:
  Elite:
    Zebra:
      patterns:
        - "elite.*zebra"
"""
        handles_file = tmp_path / "handles.yaml"
        handles_file.write_text(handles_yaml)

        matcher = HandleMatcher(handles_path=handles_file)
        result = matcher.match_handle_maker("Elite Zebra Handle")

        assert isinstance(result, dict)
        assert result is not None
        assert result["handle_maker"] == "Elite"
        assert result["handle_model"] == "Zebra"
        assert result["_matched_by_section"] == "artisan_handles"
