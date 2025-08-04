"""
Unit tests for brush scoring functions.

Tests the BrushScoringFunctions class for individual scoring calculations
and the convenience functions for direct use.
"""

import tempfile
import yaml
from pathlib import Path

from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.brush_scoring_functions import (
    BrushScoringFunctions,
    calculate_bonus_score,
    calculate_penalty_score,
    get_strategy_base_score,
)
from sotd.match.types import MatchResult


class TestBrushScoringFunctions:
    """Test cases for BrushScoringFunctions class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a valid config for testing
        self.valid_config = {
            "base_strategy_scores": {
                "strategy1": 100.0,
                "strategy2": 80.0
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
        self.scoring_functions = BrushScoringFunctions(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, 'config_path') and self.config_path.exists():
            self.config_path.unlink()
    
    def test_init(self):
        """Test BrushScoringFunctions initialization."""
        assert self.scoring_functions.config == self.config
        assert hasattr(self.scoring_functions, '_fiber_patterns')
        assert hasattr(self.scoring_functions, '_size_patterns')
        assert hasattr(self.scoring_functions, '_generic_terms')
        assert hasattr(self.scoring_functions, '_delimiter_patterns')
    
    def test_calculate_bonus_score_no_match(self):
        """Test bonus score calculation with no match."""
        match_result = MatchResult(original="test", matched=None)
        bonus_score = self.scoring_functions.calculate_bonus_score(match_result, "test")
        assert bonus_score == 0.0
    
    def test_calculate_bonus_score_with_match(self):
        """Test bonus score calculation with match."""
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand", "model": "TestModel"},
            pattern="test_pattern"
        )
        bonus_score = self.scoring_functions.calculate_bonus_score(match_result, "test")
        # Should have brand_match bonus (15.0)
        assert bonus_score >= 15.0
    
    def test_calculate_penalty_score_no_match(self):
        """Test penalty score calculation with no match."""
        match_result = MatchResult(original="test", matched=None)
        penalty_score = self.scoring_functions.calculate_penalty_score(match_result, "test")
        assert penalty_score == 0.0
    
    def test_calculate_penalty_score_with_match(self):
        """Test penalty score calculation with match."""
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand"},  # No model, should get penalty
            pattern="test_pattern"
        )
        penalty_score = self.scoring_functions.calculate_penalty_score(match_result, "test")
        # Should have single_brand_only penalty (-15.0) and no_fiber_detected penalty (-10.0)
        assert penalty_score <= -15.0
    
    def test_bonus_delimiters_present(self):
        """Test bonus calculation for delimiters."""
        # Test with delimiter
        bonus = self.scoring_functions._bonus_delimiters_present("handle in knot")
        assert bonus == 10.0
        
        # Test without delimiter
        bonus = self.scoring_functions._bonus_delimiters_present("handle knot")
        assert bonus == 0.0
        
        # Test with "with" delimiter
        bonus = self.scoring_functions._bonus_delimiters_present("handle with knot")
        assert bonus == 10.0
    
    def test_bonus_brand_match(self):
        """Test bonus calculation for brand match."""
        # Test with brand
        bonus = self.scoring_functions._bonus_brand_match({"brand": "TestBrand"})
        assert bonus == 15.0
        
        # Test without brand
        bonus = self.scoring_functions._bonus_brand_match({"model": "TestModel"})
        assert bonus == 0.0
    
    def test_bonus_fiber_words(self):
        """Test bonus calculation for fiber words."""
        # Test with fiber word
        bonus = self.scoring_functions._bonus_fiber_words("badger brush")
        assert bonus == 8.0
        
        bonus = self.scoring_functions._bonus_fiber_words("synthetic knot")
        assert bonus == 8.0
        
        # Test without fiber word
        bonus = self.scoring_functions._bonus_fiber_words("test brush")
        assert bonus == 0.0
    
    def test_bonus_size_specification(self):
        """Test bonus calculation for size specification."""
        # Test with knot size in matched data
        bonus = self.scoring_functions._bonus_size_specification(
            {"knot_size_mm": 24.0}, "test"
        )
        assert bonus == 12.0
        
        # Test with size pattern in original value
        bonus = self.scoring_functions._bonus_size_specification(
            {}, "24mm brush"
        )
        assert bonus == 12.0
        
        # Test without size
        bonus = self.scoring_functions._bonus_size_specification({}, "test brush")
        assert bonus == 0.0
    
    def test_bonus_handle_maker_match(self):
        """Test bonus calculation for handle maker match."""
        # Test with handle maker
        bonus = self.scoring_functions._bonus_handle_maker_match({"handle_maker": "TestMaker"})
        assert bonus == 10.0
        
        # Test without handle maker
        bonus = self.scoring_functions._bonus_handle_maker_match({"brand": "TestBrand"})
        assert bonus == 0.0
    
    def test_bonus_knot_maker_match(self):
        """Test bonus calculation for knot maker match."""
        # Test with knot maker
        bonus = self.scoring_functions._bonus_knot_maker_match({"knot_maker": "TestMaker"})
        assert bonus == 10.0
        
        # Test without knot maker
        bonus = self.scoring_functions._bonus_knot_maker_match({"brand": "TestBrand"})
        assert bonus == 0.0
    
    def test_bonus_exact_pattern_match(self):
        """Test bonus calculation for exact pattern match."""
        # Test with exact pattern match
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand"},
            pattern="test"
        )
        bonus = self.scoring_functions._bonus_exact_pattern_match(match_result, "test brush")
        assert bonus == 20.0
        
        # Test without exact pattern match
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand"},
            pattern="different"
        )
        bonus = self.scoring_functions._bonus_exact_pattern_match(match_result, "test brush")
        assert bonus == 0.0
    
    def test_penalty_single_brand_only(self):
        """Test penalty calculation for single brand only."""
        # Test with brand only (no model)
        penalty = self.scoring_functions._penalty_single_brand_only({"brand": "TestBrand"})
        assert penalty == -15.0
        
        # Test with brand and model
        penalty = self.scoring_functions._penalty_single_brand_only({
            "brand": "TestBrand", "model": "TestModel"
        })
        assert penalty == 0.0
    
    def test_penalty_no_fiber_detected(self):
        """Test penalty calculation for no fiber detected."""
        # Test without fiber
        penalty = self.scoring_functions._penalty_no_fiber_detected({"brand": "TestBrand"})
        assert penalty == -10.0
        
        # Test with fiber
        penalty = self.scoring_functions._penalty_no_fiber_detected({
            "brand": "TestBrand", "fiber": "badger"
        })
        assert penalty == 0.0
    
    def test_penalty_no_size_detected(self):
        """Test penalty calculation for no size detected."""
        # Test without size
        penalty = self.scoring_functions._penalty_no_size_detected({"brand": "TestBrand"})
        assert penalty == -8.0
        
        # Test with size
        penalty = self.scoring_functions._penalty_no_size_detected({
            "brand": "TestBrand", "knot_size_mm": 24.0
        })
        assert penalty == 0.0
    
    def test_penalty_fuzzy_match(self):
        """Test penalty calculation for fuzzy match."""
        # Test with fuzzy match
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand"},
            pattern="different"
        )
        penalty = self.scoring_functions._penalty_fuzzy_match(match_result, "test brush")
        assert penalty == -5.0
        
        # Test with exact match
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand"},
            pattern="test"
        )
        penalty = self.scoring_functions._penalty_fuzzy_match(match_result, "test brush")
        assert penalty == 0.0
    
    def test_penalty_generic_terms(self):
        """Test penalty calculation for generic terms."""
        # Test with generic terms
        penalty = self.scoring_functions._penalty_generic_terms("test brush")
        assert penalty == -12.0
        
        penalty = self.scoring_functions._penalty_generic_terms("test knot")
        assert penalty == -12.0
        
        # Test without generic terms
        penalty = self.scoring_functions._penalty_generic_terms("test item")
        assert penalty == 0.0
    
    def test_penalty_incomplete_specs(self):
        """Test penalty calculation for incomplete specifications."""
        # Test with incomplete specs
        penalty = self.scoring_functions._penalty_incomplete_specs({"brand": "TestBrand"})
        assert penalty == -10.0
        
        # Test with complete specs
        penalty = self.scoring_functions._penalty_incomplete_specs({
            "brand": "TestBrand", "model": "TestModel", "fiber": "badger"
        })
        assert penalty == 0.0
    
    def test_get_strategy_base_score(self):
        """Test getting strategy base score."""
        score = self.scoring_functions.get_strategy_base_score("strategy1")
        assert score == 100.0
        
        score = self.scoring_functions.get_strategy_base_score("strategy2")
        assert score == 80.0
        
        score = self.scoring_functions.get_strategy_base_score("unknown_strategy")
        assert score == 0.0
    
    def test_calculate_total_score(self):
        """Test calculating total score from components."""
        # Test normal calculation
        total = self.scoring_functions.calculate_total_score(100.0, 20.0, -10.0)
        assert total == 110.0
        
        # Test with minimum threshold
        total = self.scoring_functions.calculate_total_score(10.0, 5.0, -5.0)
        assert total == 30.0  # Minimum threshold applied


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a valid config for testing
        self.valid_config = {
            "base_strategy_scores": {"strategy1": 100.0},
            "bonus_factors": {"brand_match": 15.0},
            "penalty_factors": {"single_brand_only": -15.0},
            "routing_rules": {"minimum_score_threshold": 30.0},
            "performance": {"enable_caching": True, "cache_ttl_seconds": 3600, "max_cache_size": 10000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            self.config_path = Path(f.name)
        
        self.config = BrushScoringConfig(self.config_path)
        self.config.load_config()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, 'config_path') and self.config_path.exists():
            self.config_path.unlink()
    
    def test_calculate_bonus_score_function(self):
        """Test calculate_bonus_score convenience function."""
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand"},
            pattern="test"
        )
        bonus_score = calculate_bonus_score(match_result, "test", self.config)
        assert bonus_score >= 15.0  # brand_match bonus
    
    def test_calculate_penalty_score_function(self):
        """Test calculate_penalty_score convenience function."""
        match_result = MatchResult(
            original="test",
            matched={"brand": "TestBrand"},  # No model
            pattern="test"
        )
        penalty_score = calculate_penalty_score(match_result, "test", self.config)
        # single_brand_only penalty
        assert penalty_score <= -15.0
    
    def test_get_strategy_base_score_function(self):
        """Test get_strategy_base_score convenience function."""
        score = get_strategy_base_score("strategy1", self.config)
        assert score == 100.0
        
        score = get_strategy_base_score("unknown_strategy", self.config)
        assert score == 0.0 