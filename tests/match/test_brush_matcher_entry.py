"""
Unit tests for BrushMatcherEntryPoint.

Tests the entry point that chooses between old and new brush matching systems.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from sotd.match.brush_matcher_entry import BrushMatcherEntryPoint
from sotd.match.types import MatchResult


class TestBrushMatcherEntryPoint:
    """Test the BrushMatcherEntryPoint class."""

    def test_init_with_old_system(self):
        """Test initialization with old system (default)."""
        entry_point = BrushMatcherEntryPoint(use_scoring_system=False)
        assert entry_point.use_scoring_system is False
        assert hasattr(entry_point.matcher, "match")
        assert hasattr(entry_point.matcher, "get_cache_stats")

    def test_init_with_new_system(self):
        """Test initialization with new scoring system."""
        with patch("sotd.match.scoring_brush_matcher.BrushScoringMatcher") as mock_scoring:
            mock_scoring.return_value = Mock()
            entry_point = BrushMatcherEntryPoint(use_scoring_system=True)
            assert entry_point.use_scoring_system is True
            mock_scoring.assert_called_once()

    def test_init_passes_kwargs_to_matchers(self):
        """Test that kwargs are passed to the appropriate matcher."""
        test_kwargs = {
            "catalog_path": Path("/test/catalog.yaml"),
            "handles_path": Path("/test/handles.yaml"),
            "knots_path": Path("/test/knots.yaml"),
            "correct_matches_path": Path("/test/correct_matches.yaml"),
            "debug": True,
        }

        with patch("sotd.match.brush_matcher_entry.BrushMatcher") as mock_old:
            mock_old.return_value = Mock()
            entry_point = BrushMatcherEntryPoint(use_scoring_system=False, **test_kwargs)
            mock_old.assert_called_once_with(**test_kwargs)

        with patch("sotd.match.scoring_brush_matcher.BrushScoringMatcher") as mock_new:
            mock_new.return_value = Mock()
            entry_point = BrushMatcherEntryPoint(use_scoring_system=True, **test_kwargs)
            mock_new.assert_called_once_with(**test_kwargs)

    def test_match_delegates_to_old_system(self):
        """Test that match() delegates to old system when use_scoring_system=False."""
        mock_old_matcher = Mock()
        mock_old_matcher.match.return_value = MatchResult(
            original="test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="exact",
            pattern="test",
        )

        with patch("sotd.match.brush_matcher_entry.BrushMatcher", return_value=mock_old_matcher):
            entry_point = BrushMatcherEntryPoint(use_scoring_system=False)
            result = entry_point.match("test brush")

            mock_old_matcher.match.assert_called_once_with("test brush")
            assert result == mock_old_matcher.match.return_value

    def test_match_delegates_to_new_system(self):
        """Test that match() delegates to new system when use_scoring_system=True."""
        mock_new_matcher = Mock()
        mock_new_matcher.match.return_value = MatchResult(
            original="test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="exact",
            pattern="test",
        )

        with patch(
            "sotd.match.scoring_brush_matcher.BrushScoringMatcher", return_value=mock_new_matcher
        ):
            entry_point = BrushMatcherEntryPoint(use_scoring_system=True)
            result = entry_point.match("test brush")

            mock_new_matcher.match.assert_called_once_with("test brush")
            assert result == mock_new_matcher.match.return_value

    def test_get_cache_stats_delegates_to_old_system(self):
        """Test that get_cache_stats() delegates to old system."""
        mock_old_matcher = Mock()
        mock_old_matcher.get_cache_stats.return_value = {"hits": 10, "misses": 5}

        with patch("sotd.match.brush_matcher_entry.BrushMatcher", return_value=mock_old_matcher):
            entry_point = BrushMatcherEntryPoint(use_scoring_system=False)
            stats = entry_point.get_cache_stats()

            mock_old_matcher.get_cache_stats.assert_called_once()
            assert stats == {"hits": 10, "misses": 5}

    def test_get_cache_stats_delegates_to_new_system(self):
        """Test that get_cache_stats() delegates to new system."""
        mock_new_matcher = Mock()
        mock_new_matcher.get_cache_stats.return_value = {"hits": 15, "misses": 3}

        with patch(
            "sotd.match.scoring_brush_matcher.BrushScoringMatcher", return_value=mock_new_matcher
        ):
            entry_point = BrushMatcherEntryPoint(use_scoring_system=True)
            stats = entry_point.get_cache_stats()

            mock_new_matcher.get_cache_stats.assert_called_once()
            assert stats == {"hits": 15, "misses": 3}

    def test_system_identification(self):
        """Test that the entry point correctly identifies which system is being used."""
        with patch("sotd.match.brush_matcher_entry.BrushMatcher") as mock_old:
            mock_old.return_value = Mock()
            entry_point = BrushMatcherEntryPoint(use_scoring_system=False)
            assert entry_point.get_system_name() == "legacy"

        with patch("sotd.match.scoring_brush_matcher.BrushScoringMatcher") as mock_new:
            mock_new.return_value = Mock()
            entry_point = BrushMatcherEntryPoint(use_scoring_system=True)
            assert entry_point.get_system_name() == "scoring"

    def test_output_format_compatibility(self):
        """Test that both systems produce compatible output formats."""
        test_input = "test brush"
        expected_result = MatchResult(
            original=test_input,
            matched={"brand": "Test", "model": "Brush"},
            match_type="exact",
            pattern="test",
        )

        # Test old system
        with patch("sotd.match.brush_matcher_entry.BrushMatcher") as mock_old:
            mock_old.return_value = Mock()
            mock_old.return_value.match.return_value = expected_result
            entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
            result_old = entry_point_old.match(test_input)
            assert result_old == expected_result

        # Test new system
        with patch("sotd.match.scoring_brush_matcher.BrushScoringMatcher") as mock_new:
            mock_new.return_value = Mock()
            mock_new.return_value.match.return_value = expected_result
            entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
            result_new = entry_point_new.match(test_input)
            assert result_new == expected_result

    def test_error_handling_old_system(self):
        """Test error handling when old system raises an exception."""
        mock_old_matcher = Mock()
        mock_old_matcher.match.side_effect = ValueError("Test error")

        with patch("sotd.match.brush_matcher_entry.BrushMatcher", return_value=mock_old_matcher):
            entry_point = BrushMatcherEntryPoint(use_scoring_system=False)
            with pytest.raises(ValueError, match="Test error"):
                entry_point.match("test brush")

    def test_error_handling_new_system(self):
        """Test error handling when new system raises an exception."""
        mock_new_matcher = Mock()
        mock_new_matcher.match.side_effect = ValueError("Test error")

        with patch(
            "sotd.match.scoring_brush_matcher.BrushScoringMatcher", return_value=mock_new_matcher
        ):
            entry_point = BrushMatcherEntryPoint(use_scoring_system=True)
            with pytest.raises(ValueError, match="Test error"):
                entry_point.match("test brush")
