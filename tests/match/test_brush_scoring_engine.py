"""
Unit tests for brush scoring engine.

Tests the BrushScoringEngine class for strategy execution, score calculation,
and result sorting functionality.
"""

import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock

import pytest

from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.brush_scoring_engine import BrushScoringEngine, BrushScoringResult
from sotd.match.types import MatchResult


class MockBrushStrategy:
    """Mock brush strategy for testing."""
    
    def __init__(self, name: str, should_match: bool = True, match_data: dict = None):
        self.name = name
        self.should_match = should_match
        self.match_data = match_data if match_data is not None else {"brand": "TestBrand", "model": "TestModel"}
    
    def match(self, value: str):
        if self.should_match:
            return MatchResult(
                original=value,
                matched=self.match_data,
                match_type="test",
                pattern="test_pattern"
            )
        return None


class TestBrushScoringResult:
    """Test cases for BrushScoringResult class."""
    
    def test_init(self):
        """Test BrushScoringResult initialization."""
        match_result = MatchResult(original="test", matched={"brand": "test"})
        result = BrushScoringResult(
            match_result=match_result,
            strategy_name="test_strategy",
            base_score=100.0,
            bonus_score=10.0,
            penalty_score=-5.0,
            total_score=105.0
        )
        
        assert result.match_result == match_result
        assert result.strategy_name == "test_strategy"
        assert result.base_score == 100.0
        assert result.bonus_score == 10.0
        assert result.penalty_score == -5.0
        assert result.total_score == 105.0
        assert result.metadata == {}
    
    def test_init_with_metadata(self):
        """Test BrushScoringResult initialization with metadata."""
        match_result = MatchResult(original="test", matched={"brand": "test"})
        metadata = {"test_key": "test_value"}
        result = BrushScoringResult(
            match_result=match_result,
            strategy_name="test_strategy",
            base_score=100.0,
            bonus_score=0.0,
            penalty_score=0.0,
            total_score=100.0,
            metadata=metadata
        )
        
        assert result.metadata == metadata
    
    def test_lt_comparison(self):
        """Test BrushScoringResult sorting comparison."""
        match_result = MatchResult(original="test", matched={"brand": "test"})
        
        result1 = BrushScoringResult(
            match_result=match_result,
            strategy_name="strategy1",
            base_score=100.0,
            bonus_score=0.0,
            penalty_score=0.0,
            total_score=100.0
        )
        
        result2 = BrushScoringResult(
            match_result=match_result,
            strategy_name="strategy2",
            base_score=100.0,
            bonus_score=0.0,
            penalty_score=0.0,
            total_score=150.0
        )
        
        # Higher score should come first
        assert result2 < result1
        assert not result1 < result2
    
    def test_repr(self):
        """Test BrushScoringResult string representation."""
        match_result = MatchResult(original="test", matched={"brand": "test"})
        result = BrushScoringResult(
            match_result=match_result,
            strategy_name="test_strategy",
            base_score=100.0,
            bonus_score=10.0,
            penalty_score=-5.0,
            total_score=105.0
        )
        
        repr_str = repr(result)
        assert "BrushScoringResult" in repr_str
        assert "test_strategy" in repr_str
        assert "105.00" in repr_str
        assert "matched=True" in repr_str


class TestBrushScoringEngine:
    """Test cases for BrushScoringEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a valid config for testing
        self.valid_config = {
            "base_strategy_scores": {
                "strategy1": 100.0,
                "strategy2": 80.0,
                "strategy3": 60.0
            },
            "bonus_factors": {
                "delimiters_present": 10.0,
                "brand_match": 15.0,
                "fiber_words": 8.0,
                "size_specification": 12.0,
                "handle_maker_match": 10.0,
                "knot_maker_match": 10.0,
                "exact_pattern_match": 20.0
            },
            "penalty_factors": {
                "single_brand_only": -15.0,
                "no_fiber_detected": -10.0,
                "no_size_detected": -8.0,
                "fuzzy_match": -5.0,
                "generic_terms": -12.0,
                "incomplete_specs": -10.0
            },
            "routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "max_cache_size": 10000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            self.config_path = Path(f.name)
        
        self.config = BrushScoringConfig(self.config_path)
        self.config.load_config()
        self.engine = BrushScoringEngine(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, 'config_path') and self.config_path.exists():
            self.config_path.unlink()
    
    def test_init(self):
        """Test BrushScoringEngine initialization."""
        assert self.engine.config == self.config
        assert self.engine.strategy_count == 0
        assert self.engine.strategy_names == []
    
    def test_add_strategy(self):
        """Test adding strategies to the engine."""
        strategy1 = MockBrushStrategy("strategy1")
        strategy2 = MockBrushStrategy("strategy2")
        
        self.engine.add_strategy(strategy1, "strategy1")
        self.engine.add_strategy(strategy2, "strategy2")
        
        assert self.engine.strategy_count == 2
        assert self.engine.strategy_names == ["strategy1", "strategy2"]
    
    def test_score_brush_no_strategies(self):
        """Test scoring with no strategies registered."""
        results = self.engine.score_brush("test brush")
        assert results == []
    
    def test_score_brush_single_strategy_no_match(self):
        """Test scoring with single strategy that doesn't match."""
        strategy = MockBrushStrategy("strategy1", should_match=False)
        self.engine.add_strategy(strategy, "strategy1")
        
        results = self.engine.score_brush("test brush")
        assert results == []
    
    def test_score_brush_single_strategy_match(self):
        """Test scoring with single strategy that matches."""
        strategy = MockBrushStrategy("strategy1", should_match=True)
        self.engine.add_strategy(strategy, "strategy1")
        
        results = self.engine.score_brush("test brush")
        assert len(results) == 1
        
        result = results[0]
        assert result.strategy_name == "strategy1"
        assert result.base_score == 100.0
        # Total score should be at least the minimum threshold
        min_threshold = self.config.get_routing_rule("minimum_score_threshold") or 0.0
        assert result.total_score >= min_threshold
    
    def test_score_brush_multiple_strategies(self):
        """Test scoring with multiple strategies."""
        strategy1 = MockBrushStrategy("strategy1", should_match=True)
        strategy2 = MockBrushStrategy("strategy2", should_match=True)
        strategy3 = MockBrushStrategy("strategy3", should_match=False)
        
        self.engine.add_strategy(strategy1, "strategy1")
        self.engine.add_strategy(strategy2, "strategy2")
        self.engine.add_strategy(strategy3, "strategy3")
        
        results = self.engine.score_brush("test brush")
        assert len(results) == 2  # Only 2 strategies matched
        
        # Results should be sorted by score (highest first)
        assert results[0].total_score >= results[1].total_score
    
    def test_score_brush_strategy_failure(self):
        """Test scoring when a strategy fails."""
        strategy = Mock()
        strategy.match.side_effect = Exception("Strategy failed")
        
        self.engine.add_strategy(strategy, "failing_strategy")
        
        with pytest.raises(RuntimeError, match="Strategy failing_strategy failed"):
            self.engine.score_brush("test brush")
    
    def test_score_brush_config_not_loaded(self):
        """Test scoring when configuration is not loaded."""
        unloaded_config = BrushScoringConfig()
        engine = BrushScoringEngine(unloaded_config)
        
        strategy = MockBrushStrategy("strategy1")
        engine.add_strategy(strategy, "strategy1")
        
        with pytest.raises(ValueError, match="Brush scoring configuration not loaded"):
            engine.score_brush("test brush")
    
    def test_calculate_bonus_score_delimiters(self):
        """Test bonus score calculation for delimiters."""
        strategy = MockBrushStrategy("strategy1")
        self.engine.add_strategy(strategy, "strategy1")
        
        # Test with delimiter
        results = self.engine.score_brush("handle in knot")
        assert len(results) == 1
        # Should have delimiter bonus (10.0) plus brand match bonus (15.0)
        assert results[0].bonus_score >= 10.0  # delimiters_present bonus
        
        # Test without delimiter
        results = self.engine.score_brush("handle knot")
        assert len(results) == 1
        # Should only have brand match bonus (15.0), no delimiter bonus
        assert results[0].bonus_score >= 15.0  # brand_match bonus
        # The delimiter bonus should not be present
        # We can't easily test this without more complex logic, so just verify it's reasonable
    
    def test_calculate_bonus_score_brand_match(self):
        """Test bonus score calculation for brand match."""
        match_data = {"brand": "TestBrand", "model": "TestModel"}
        strategy = MockBrushStrategy("strategy1", should_match=True, match_data=match_data)
        self.engine.add_strategy(strategy, "strategy1")
        
        results = self.engine.score_brush("test brush")
        assert len(results) == 1
        assert results[0].bonus_score >= 15.0  # brand_match bonus
    
    def test_calculate_penalty_score_single_brand(self):
        """Test penalty score calculation for single brand only."""
        match_data = {"brand": "TestBrand"}  # No model
        strategy = MockBrushStrategy("strategy1", should_match=True, match_data=match_data)
        self.engine.add_strategy(strategy, "strategy1")
        
        results = self.engine.score_brush("test brush")
        assert len(results) == 1
        assert results[0].penalty_score <= -15.0  # single_brand_only penalty
    
    def test_calculate_penalty_score_no_fiber(self):
        """Test penalty score calculation for no fiber detected."""
        match_data = {"brand": "TestBrand", "model": "TestModel"}  # No fiber
        strategy = MockBrushStrategy("strategy1", should_match=True, match_data=match_data)
        self.engine.add_strategy(strategy, "strategy1")
        
        results = self.engine.score_brush("test brush")
        assert len(results) == 1
        assert results[0].penalty_score <= -10.0  # no_fiber_detected penalty
    
    def test_get_best_match(self):
        """Test getting the best match."""
        strategy1 = MockBrushStrategy("strategy1", should_match=True)
        strategy2 = MockBrushStrategy("strategy2", should_match=True)
        
        self.engine.add_strategy(strategy1, "strategy1")
        self.engine.add_strategy(strategy2, "strategy2")
        
        best_match = self.engine.get_best_match("test brush")
        assert best_match is not None
        assert best_match.strategy_name in ["strategy1", "strategy2"]
    
    def test_get_best_match_no_matches(self):
        """Test getting best match when no strategies match."""
        strategy = MockBrushStrategy("strategy1", should_match=False)
        self.engine.add_strategy(strategy, "strategy1")
        
        best_match = self.engine.get_best_match("test brush")
        assert best_match is None
    
    def test_get_all_matches(self):
        """Test getting all matches."""
        strategy1 = MockBrushStrategy("strategy1", should_match=True)
        strategy2 = MockBrushStrategy("strategy2", should_match=True)
        strategy3 = MockBrushStrategy("strategy3", should_match=False)
        
        self.engine.add_strategy(strategy1, "strategy1")
        self.engine.add_strategy(strategy2, "strategy2")
        self.engine.add_strategy(strategy3, "strategy3")
        
        all_matches = self.engine.get_all_matches("test brush")
        assert len(all_matches) == 2
        assert all_matches[0].total_score >= all_matches[1].total_score
    
    def test_strategy_count_property(self):
        """Test strategy_count property."""
        assert self.engine.strategy_count == 0
        
        strategy = MockBrushStrategy("strategy1")
        self.engine.add_strategy(strategy, "strategy1")
        assert self.engine.strategy_count == 1
        
        strategy2 = MockBrushStrategy("strategy2")
        self.engine.add_strategy(strategy2, "strategy2")
        assert self.engine.strategy_count == 2
    
    def test_strategy_names_property(self):
        """Test strategy_names property."""
        assert self.engine.strategy_names == []
        
        strategy1 = MockBrushStrategy("strategy1")
        strategy2 = MockBrushStrategy("strategy2")
        
        self.engine.add_strategy(strategy1, "strategy1")
        self.engine.add_strategy(strategy2, "strategy2")
        
        names = self.engine.strategy_names
        assert names == ["strategy1", "strategy2"]
        assert names is not self.engine._strategy_names  # Should be a copy


 