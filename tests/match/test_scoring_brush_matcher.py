"""
Unit tests for scoring brush matcher.

Tests the ScoringBrushMatcher class for integration with existing pipeline
and scoring system functionality.
"""

import tempfile
import yaml
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pytest


from sotd.match.config import BrushMatcherConfig
from sotd.match.scoring_brush_matcher import ScoringBrushMatcher
from sotd.match.types import MatchResult


class MockBrushStrategy:
    """Mock brush strategy for testing."""

    def __init__(self, name: str, should_match: bool = True, match_data: Optional[dict] = None):
        self.name = name
        self.should_match = should_match
        self.match_data = match_data or {"brand": "TestBrand", "model": "TestModel"}

    def match(self, value: str):
        if self.should_match:
            return MatchResult(
                original=value, matched=self.match_data, match_type="test", pattern="test_pattern"
            )
        return None


class TestScoringBrushMatcher:
    """Test cases for ScoringBrushMatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a valid scoring config for testing
        self.valid_scoring_config = {
            "brush_scoring_weights": {
                "base_strategies": {
                    "correct_complete_brush": 90.0,
                    "correct_split_brush": 85.0,
                    "known_split": 80.0,
                    "high_priority_automated_split": 75.0,
                    "complete_brush": 70.0,
                    "dual_component": 65.0,
                    "medium_priority_automated_split": 60.0,
                    "single_component_fallback": 55.0,
                },
                "strategy_modifiers": {
                    "high_priority_automated_split": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "medium_priority_automated_split": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "dual_component": {
                        "high_priority_delimiter": 0.0,
                        "medium_priority_delimiter": 0.0,
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                        "handle_knot_words": 0.0,
                    },
                    "complete_brush": {
                        "high_priority_delimiter": 0.0,
                        "medium_priority_delimiter": 0.0,
                        "multiple_brands": 0.0,
                        "handle_knot_words": 0.0,
                        "fiber_words": 0.0,
                    },
                },
            },
            "brush_routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.valid_scoring_config, f)
            self.scoring_config_path = Path(f.name)

        # Create mock catalog data
        self.mock_catalog_data = {
            "brushes": {
                "known_brushes": {"TestBrand": {"TestModel": {"patterns": ["test_pattern"]}}},
                "other_brushes": {},
            },
            "knots": {"known_knots": {}, "other_knots": {}},
            "correct_matches": {"brush": {"ExactBrand": {"ExactModel": ["exact_match"]}}},
        }

    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, "scoring_config_path") and self.scoring_config_path.exists():
            self.scoring_config_path.unlink()

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_init(self, mock_cache, mock_checker, mock_loader):
        """Test ScoringBrushMatcher initialization."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        assert matcher.scoring_config.is_loaded
        assert matcher.catalog_data == self.mock_catalog_data["brushes"]
        assert matcher.knots_data == self.mock_catalog_data["knots"]
        assert matcher.correct_matches == self.mock_catalog_data["correct_matches"]
        assert matcher.strategy_count > 0

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_init_with_config(self, mock_cache, mock_checker, mock_loader):
        """Test initialization with BrushMatcherConfig."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        config = BrushMatcherConfig.create_custom(debug=True)
        matcher = ScoringBrushMatcher(config=config, scoring_config_path=self.scoring_config_path)

        assert matcher.config == config
        assert matcher.debug is True

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_init_invalid_scoring_config(self, mock_cache, mock_checker, mock_loader):
        """Test initialization with invalid scoring configuration."""
        # Create invalid config
        invalid_config = {"invalid": "config"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(invalid_config, f)
            invalid_config_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid scoring configuration"):
                ScoringBrushMatcher(scoring_config_path=invalid_config_path)
        finally:
            invalid_config_path.unlink()

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_match_cached_result(self, mock_cache, mock_checker, mock_loader):
        """Test matching with cached result."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache with cached result
        mock_cache_instance = Mock()
        cached_result = MatchResult(original="test", matched={"brand": "Cached"})
        mock_cache_instance.get.return_value = cached_result
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        result = matcher.match("test")

        assert result == cached_result
        mock_cache_instance.get.assert_called_once_with("scoring_test")

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_match_exact_match_bypass(self, mock_cache, mock_checker, mock_loader):
        """Test matching with exact match bypass."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker with exact match
        mock_checker_instance = Mock()
        exact_match = MatchResult(original="exact_match", matched={"brand": "ExactBrand"})
        mock_checker_instance.check.return_value = exact_match
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None  # No cached result
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        result = matcher.match("exact_match")

        assert result == exact_match
        mock_checker_instance.check.assert_called_once_with("exact_match")
        mock_cache_instance.set.assert_called()

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_match_no_exact_match_bypass(self, mock_cache, mock_checker, mock_loader):
        """Test matching without exact match bypass."""
        # Create config with exact_match_bypass disabled
        config_without_bypass = self.valid_scoring_config.copy()
        config_without_bypass["brush_routing_rules"]["exact_match_bypass"] = False

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_without_bypass, f)
            config_path = Path(f.name)

        try:
            # Mock the catalog loader
            mock_loader_instance = Mock()
            mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
            mock_loader.return_value = mock_loader_instance

            # Mock the correct matches checker
            mock_checker_instance = Mock()
            mock_checker_instance.check.return_value = None  # No exact match
            mock_checker.return_value = mock_checker_instance

            # Mock the cache
            mock_cache_instance = Mock()
            mock_cache_instance.get.return_value = None  # No cached result
            mock_cache.return_value = mock_cache_instance

            matcher = ScoringBrushMatcher(scoring_config_path=config_path)

            # Mock the scoring engine to return a result
            mock_result = MatchResult(original="test", matched={"brand": "TestBrand"})
            matcher.scoring_engine.score_brush = Mock(
                return_value=[
                    Mock(
                        match_result=mock_result,
                        strategy_name="test_strategy",
                        base_score=100.0,
                        bonus_score=10.0,
                        penalty_score=-5.0,
                        total_score=105.0,
                    )
                ]
            )

            result = matcher.match("test")

            assert result is not None
            assert result.matched["brand"] == "TestBrand"
            mock_checker_instance.check.assert_not_called()  # Should not be called
        finally:
            config_path.unlink()

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_match_no_results(self, mock_cache, mock_checker, mock_loader):
        """Test matching with no results from scoring engine."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker_instance.check.return_value = None  # No exact match
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None  # No cached result
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        # Mock the scoring engine to return no results
        matcher.scoring_engine.score_brush = Mock(return_value=[])

        result = matcher.match("test")

        assert result is None
        mock_cache_instance.set.assert_called_with("scoring_test", None)

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_get_all_matches(self, mock_cache, mock_checker, mock_loader):
        """Test getting all matches."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        # Mock the scoring engine
        mock_results = [Mock(), Mock()]
        matcher.scoring_engine.get_all_matches = Mock(return_value=mock_results)

        results = matcher.get_all_matches("test")

        assert results == mock_results
        matcher.scoring_engine.get_all_matches.assert_called_once_with("test")

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_get_best_match(self, mock_cache, mock_checker, mock_loader):
        """Test getting best match."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        # Mock the scoring engine
        mock_result = Mock()
        matcher.scoring_engine.get_best_match = Mock(return_value=mock_result)

        result = matcher.get_best_match("test")

        assert result == mock_result
        matcher.scoring_engine.get_best_match.assert_called_once_with("test")

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_get_cache_stats(self, mock_cache, mock_checker, mock_loader):
        """Test getting cache statistics."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_stats = {"hits": 10, "misses": 5}
        mock_cache_instance.stats.return_value = mock_stats
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        stats = matcher.get_cache_stats()

        assert stats == mock_stats
        mock_cache_instance.stats.assert_called_once()

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_clear_cache(self, mock_cache, mock_checker, mock_loader):
        """Test clearing cache."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        matcher.clear_cache()

        mock_cache_instance.clear.assert_called_once()

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_strategy_count_property(self, mock_cache, mock_checker, mock_loader):
        """Test strategy_count property."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        # Test that strategy_count property works
        assert matcher.strategy_count > 0  # Should have strategies registered

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_strategy_names_property(self, mock_cache, mock_checker, mock_loader):
        """Test strategy_names property."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        # Test that strategy_names property works
        names = matcher.strategy_names
        assert isinstance(names, list)
        assert len(names) > 0  # Should have strategy names

    @patch("sotd.match.scoring_brush_matcher.CatalogLoader")
    @patch("sotd.match.scoring_brush_matcher.CorrectMatchesChecker")
    @patch("sotd.match.scoring_brush_matcher.MatchCache")
    def test_reload_scoring_config(self, mock_cache, mock_checker, mock_loader):
        """Test reloading scoring configuration."""
        # Mock the catalog loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_all_catalogs.return_value = self.mock_catalog_data
        mock_loader.return_value = mock_loader_instance

        # Mock the correct matches checker
        mock_checker_instance = Mock()
        mock_checker.return_value = mock_checker_instance

        # Mock the cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        matcher = ScoringBrushMatcher(scoring_config_path=self.scoring_config_path)

        matcher.reload_scoring_config()

        # Should clear cache when config is reloaded
        mock_cache_instance.clear.assert_called_once()
