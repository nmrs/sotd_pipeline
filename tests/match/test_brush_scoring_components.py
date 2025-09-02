"""
Unit tests for brush scoring matcher components.

Tests individual components with single responsibilities and improved architecture.
"""

from unittest.mock import Mock

from sotd.match.brush_scoring_components.scoring_engine import ScoringEngine

from sotd.match.brush_scoring_components.correct_matches_matcher import CorrectMatchesMatcher
from sotd.match.brush_scoring_components.strategy_orchestrator import StrategyOrchestrator
from sotd.match.brush_scoring_components.performance_monitor import PerformanceMonitor
from sotd.match.types import MatchResult


class TestCorrectMatchesMatcher:
    """Test the CorrectMatchesMatcher component."""

    def test_init_with_correct_matches_data(self):
        """Test initialization with correct matches data."""
        correct_matches_data = {"brush": {"test": "data"}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        assert matcher.correct_matches == correct_matches_data

    def test_match_exact_match(self):
        """Test exact match against correct matches."""
        correct_matches_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2"]}}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("simpson chubby 2")

        assert result is not None
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"

    def test_match_no_match(self):
        """Test when no exact match is found."""
        correct_matches_data = {"brush": {}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("unknown brush")

        assert result is None

    def test_match_case_insensitive(self):
        """Test case-insensitive matching."""
        correct_matches_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2"]}}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("SIMPSON CHUBBY 2")

        assert result is not None
        assert result.matched["brand"] == "Simpson"

    def test_match_empty_input(self):
        """Test matching with empty input."""
        correct_matches_data = {"brush": {}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("")

        assert result is None


class TestStrategyOrchestrator:
    """Test the StrategyOrchestrator component."""

    def test_init_with_strategies(self):
        """Test initialization with strategies."""
        strategies = [Mock(), Mock()]
        orchestrator = StrategyOrchestrator(strategies)
        assert orchestrator.strategies == strategies

    def test_run_all_strategies(self):
        """Test running all strategies."""
        mock_strategy1 = Mock()
        mock_strategy1.match.return_value = MatchResult(
            original="test", matched={"brand": "Test1"}, match_type="exact", pattern="test1"
        )

        mock_strategy2 = Mock()
        mock_strategy2.match.return_value = MatchResult(
            original="test", matched={"brand": "Test2"}, match_type="exact", pattern="test2"
        )

        strategies = [mock_strategy1, mock_strategy2]
        orchestrator = StrategyOrchestrator(strategies)

        results = orchestrator.run_all_strategies("test brush")

        assert len(results) == 2
        assert results[0].matched["brand"] == "Test1"
        assert results[1].matched["brand"] == "Test2"

        mock_strategy1.match.assert_called_once_with("test brush")
        mock_strategy2.match.assert_called_once_with("test brush")

    def test_run_all_strategies_with_none_results(self):
        """Test running strategies that return None."""
        mock_strategy1 = Mock()
        mock_strategy1.match.return_value = None

        mock_strategy2 = Mock()
        mock_strategy2.match.return_value = MatchResult(
            original="test", matched={"brand": "Test2"}, match_type="exact", pattern="test2"
        )

        strategies = [mock_strategy1, mock_strategy2]
        orchestrator = StrategyOrchestrator(strategies)

        results = orchestrator.run_all_strategies("test brush")

        assert len(results) == 1
        assert results[0].matched["brand"] == "Test2"

    def test_run_all_strategies_empty_list(self):
        """Test running with empty strategy list."""
        orchestrator = StrategyOrchestrator([])
        results = orchestrator.run_all_strategies("test brush")

        assert results == []


class TestScoringEngine:
    """Test the ScoringEngine component."""

    def test_init_with_config(self):
        """Test initialization with configuration."""
        mock_config = Mock()
        engine = ScoringEngine(mock_config)
        assert engine.config == mock_config

    def test_score_results(self):
        """Test scoring strategy results."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 80.0
        mock_config.get_strategy_modifier.return_value = 5.0
        mock_config.get_all_modifier_names.return_value = ["test_modifier"]

        engine = ScoringEngine(mock_config)

        results = [
            MatchResult(
                original="test",
                matched={"brand": "Test1"},
                match_type="exact",
                pattern="test1",
                strategy="test_strategy",
            ),
            MatchResult(
                original="test",
                matched={"brand": "Test2"},
                match_type="exact",
                pattern="test2",
                strategy="test_strategy",
            ),
        ]

        scored_results = engine.score_results(results, "test brush")

        assert len(scored_results) == 2
        assert all(hasattr(result, "score") for result in scored_results)
        assert all(result.score > 0 for result in scored_results)

    def test_get_best_result(self):
        """Test getting the best result."""
        mock_config = Mock()
        engine = ScoringEngine(mock_config)

        # Create results with different scores
        result1 = Mock()
        result1.score = 85.0

        result2 = Mock()
        result2.score = 90.0

        result3 = Mock()
        result3.score = 75.0

        scored_results = [result1, result2, result3]
        best_result = engine.get_best_result(scored_results)

        assert best_result == result2  # Highest score

    def test_get_best_result_empty_list(self):
        """Test getting best result from empty list."""
        mock_config = Mock()
        engine = ScoringEngine(mock_config)

        best_result = engine.get_best_result([])
        assert best_result is None

    def test_score_results_with_modifiers(self):
        """Test scoring with strategy modifiers."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 80.0
        mock_config.get_strategy_modifier.return_value = 10.0
        mock_config.get_all_modifier_names.return_value = ["test_modifier"]

        engine = ScoringEngine(mock_config)

        result = MatchResult(
            original="test",
            matched={
                "brand": "Test",
                "handle": {"brand": None, "model": None},
                "knot": {"brand": "Test", "model": None, "fiber": "badger", "knot_size_mm": None},
            },
            match_type="exact",
            pattern="test",
            strategy="test_strategy",
        )

        scored_results = engine.score_results([result], "test brush")

        assert len(scored_results) == 1
        assert scored_results[0].score >= 80.0  # Base score plus modifiers

    def test_modifier_handle_brand_without_knot_brand(self):
        """Test handle brand without knot brand modifier for handle_only strategy."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 40.0
        mock_config.get_strategy_modifier.return_value = 25.0
        mock_config.get_all_modifier_names.return_value = ["handle_brand_without_knot_brand"]

        engine = ScoringEngine(mock_config)

        # Mock cached_results with unified strategy results
        mock_unified_result = Mock()
        mock_unified_result.matched = {
            "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
            "knot": {"brand": None, "fiber": "badger"},
        }
        engine.cached_results = {"full_input_component_matching_result": mock_unified_result}

        result = MatchResult(
            original="Farvour Turn Craft 26mm",
            matched={
                "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
                "knot": {"brand": None, "fiber": "badger"},
            },
            match_type="handle_only",
            pattern="handle_only",
            strategy="handle_only",
        )

        scored_results = engine.score_results(
            [result], "Farvour Turn Craft 26mm", engine.cached_results
        )

        assert len(scored_results) == 1
        # Base score (40.0) + modifier (25.0) = 65.0
        assert scored_results[0].score == 65.0

    def test_modifier_handle_brand_without_knot_brand_wrong_strategy(self):
        """Test handle brand without knot brand modifier doesn't apply to other strategies."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 50.0
        mock_config.get_strategy_modifier.return_value = 25.0
        mock_config.get_all_modifier_names.return_value = ["handle_brand_without_knot_brand"]

        engine = ScoringEngine(mock_config)

        result = MatchResult(
            original="Farvour Turn Craft 26mm",
            matched={
                "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
                "knot": {"brand": None, "fiber": "badger"},
            },
            match_type="unified",
            pattern="unified",
            strategy="unified",
        )

        # Create cached_results for the test
        mock_unified_result = Mock()
        mock_unified_result.matched = {
            "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
            "knot": {"brand": None, "fiber": "badger"},
        }
        cached_results = {"full_input_component_matching_result": mock_unified_result}

        scored_results = engine.score_results([result], "Farvour Turn Craft 26mm", cached_results)

        assert len(scored_results) == 1
        # Base score (50.0) only - modifier shouldn't apply to unified strategy
        assert scored_results[0].score == 50.0

    def test_modifier_knot_brand_without_handle_brand(self):
        """Test knot brand without handle brand modifier for knot_only strategy."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 40.0
        mock_config.get_strategy_modifier.return_value = 25.0
        mock_config.get_all_modifier_names.return_value = ["knot_brand_without_handle_brand"]

        engine = ScoringEngine(mock_config)

        # Mock cached_results with unified strategy results
        mock_unified_result = Mock()
        mock_unified_result.matched = {
            "handle": {"brand": None, "model": None},
            "knot": {"brand": "Declaration Grooming", "model": "B2"},
        }
        engine.cached_results = {"full_input_component_matching_result": mock_unified_result}

        result = MatchResult(
            original="Declaration B2",
            matched={
                "handle": {"brand": None, "model": None},
                "knot": {"brand": "Declaration Grooming", "model": "B2"},
            },
            match_type="knot_only",
            pattern="knot_only",
            strategy="knot_only",
        )

        scored_results = engine.score_results([result], "Declaration B2", engine.cached_results)

        assert len(scored_results) == 1
        # Base score (40.0) + modifier (25.0) = 65.0
        assert scored_results[0].score == 65.0

    def test_modifier_knot_brand_without_handle_brand_wrong_strategy(self):
        """Test knot brand without handle brand modifier doesn't apply to other strategies."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 50.0
        mock_config.get_strategy_modifier.return_value = 25.0
        mock_config.get_all_modifier_names.return_value = ["knot_brand_without_handle_brand"]

        engine = ScoringEngine(mock_config)

        result = MatchResult(
            original="Declaration B2",
            matched={
                "handle": {"brand": None, "model": None},
                "knot": {"brand": "Declaration Grooming", "model": "B2"},
            },
            match_type="unified",
            pattern="unified",
            strategy="unified",
        )

        scored_results = engine.score_results([result], "Declaration B2")

        assert len(scored_results) == 1
        # Base score (50.0) only - modifier shouldn't apply to unified strategy
        assert scored_results[0].score == 50.0

    def test_modifier_handle_brand_without_knot_brand_no_brand(self):
        """Test handle brand without knot brand modifier when no handle brand is present."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 40.0
        mock_config.get_strategy_modifier.return_value = 25.0
        mock_config.get_all_modifier_names.return_value = ["handle_brand_without_knot_brand"]

        engine = ScoringEngine(mock_config)

        result = MatchResult(
            original="Custom Wood Handle",
            matched={
                "handle": {"brand": None, "model": "Custom"},
                "knot": {"brand": None, "fiber": None},
            },
            match_type="handle_only",
            pattern="handle_only",
            strategy="handle_only",
        )

        scored_results = engine.score_results([result], "Custom Wood Handle")

        assert len(scored_results) == 1
        # Base score (40.0) only - no modifier applied because no handle brand
        assert scored_results[0].score == 40.0

    def test_modifier_knot_brand_without_handle_brand_no_brand(self):
        """Test knot brand without handle brand modifier when no knot brand is present."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 40.0
        mock_config.get_strategy_modifier.return_value = 25.0
        mock_config.get_all_modifier_names.return_value = ["knot_brand_without_handle_brand"]

        engine = ScoringEngine(mock_config)

        result = MatchResult(
            original="26mm Badger Knot",
            matched={
                "handle": {"brand": None, "model": None},
                "knot": {"brand": None, "fiber": "badger", "knot_size_mm": 26},
            },
            match_type="knot_only",
            pattern="knot_only",
            strategy="knot_only",
        )

        scored_results = engine.score_results([result], "26mm Badger Knot")

        assert len(scored_results) == 1
        # Base score (40.0) only - no modifier applied because no knot brand
        assert scored_results[0].score == 40.0

    def test_brand_balance_modifiers(self):
        """Test that brand balance modifiers work correctly with cached results."""
        mock_config = Mock()
        engine = ScoringEngine(mock_config)

        # Test handle_brand_without_knot_brand modifier
        mock_unified_result = Mock()
        mock_unified_result.matched = {
            "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
            "knot": {"brand": None, "fiber": "badger"},
        }
        engine.cached_results = {"full_input_component_matching_result": mock_unified_result}

        # Should return 1.0 when handle brand is populated but knot brand is not
        assert engine._modifier_handle_brand_without_knot_brand("test", None, "handle_only") == 1.0
        assert engine._modifier_handle_brand_without_knot_brand("test", None, "knot_only") == 1.0

        # Test knot_brand_without_handle_brand modifier
        mock_unified_result.matched = {
            "handle": {"brand": None, "model": None},
            "knot": {"brand": "Declaration Grooming", "model": "B2"},
        }

        # Should return 1.0 when knot brand is populated but handle brand is not
        assert engine._modifier_knot_brand_without_handle_brand("test", None, "handle_only") == 1.0
        assert engine._modifier_knot_brand_without_handle_brand("test", None, "knot_only") == 1.0

    def test_brand_balance_modifier_math_scenarios(self):
        """Test comprehensive math scenarios for brand balance modifiers."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 40.0

        # Create a more realistic mock that handles different strategies
        def mock_get_strategy_modifier(strategy, modifier):
            if strategy == "handle_only":
                modifiers = {
                    "handle_indicators": 30.0,
                    "knot_indicators": -30.0,
                    "handle_brand_without_knot_brand": 25.0,
                    "knot_brand_without_handle_brand": -25.0,
                }
            elif strategy == "knot_only":
                modifiers = {
                    "handle_indicators": -30.0,
                    "knot_indicators": 30.0,
                    "handle_brand_without_knot_brand": -25.0,
                    "knot_brand_without_handle_brand": 25.0,
                }
            else:
                modifiers = {}
            return modifiers.get(modifier, 0.0)

        mock_config.get_strategy_modifier.side_effect = mock_get_strategy_modifier
        mock_config.get_all_modifier_names.return_value = [
            "handle_indicators",
            "knot_indicators",
            "handle_brand_without_knot_brand",
            "knot_brand_without_handle_brand",
        ]

        engine = ScoringEngine(mock_config)

        # Scenario 1: Handle brand only (Farvour Turn Craft case)
        print("\n=== Scenario 1: Handle brand only ===")
        mock_unified_result = Mock()
        mock_unified_result.matched = {
            "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
            "knot": {"brand": None, "fiber": "badger"},
        }
        engine.cached_results = {"full_input_component_matching_result": mock_unified_result}

        # Test handle_only strategy
        result_handle = MatchResult(
            original="Farvour Turn Craft 26mm",
            matched={"handle": {"brand": "Farvour Turn Craft", "model": "Custom"}},
            match_type="handle_only",
            pattern="handle_only",
            strategy="handle_only",
        )

        scored_handle = engine.score_results(
            [result_handle], "Farvour Turn Craft 26mm", engine.cached_results
        )
        score_handle = scored_handle[0].score

        # Debug: Let's see what modifiers are actually being calculated
        print(f"Debug: Testing handle_brand_without_knot_brand modifier directly...")
        modifier_value = engine._modifier_handle_brand_without_knot_brand(
            "test", result_handle, "handle_only"
        )
        modifier_weight = mock_config.get_strategy_modifier(
            "handle_only", "handle_brand_without_knot_brand"
        )
        print(f"  modifier_value: {modifier_value}")
        print(f"  modifier_weight: {modifier_weight}")
        print(f"  expected effect: {modifier_value * modifier_weight}")

        # Debug: Let's see what's happening in _calculate_modifiers
        print(f"\nDebug: Testing _calculate_modifiers method...")
        modifier_score = engine._calculate_modifiers(result_handle, "test", "handle_only")
        print(f"  _calculate_modifiers returned: {modifier_score}")

        # Debug: Let's see what modifier functions are available
        print(f"\nDebug: Available modifier functions:")
        for modifier_name in mock_config.get_all_modifier_names("handle_only"):
            modifier_function = getattr(engine, f"_modifier_{modifier_name}", None)
            print(f"  {modifier_name}: {modifier_function is not None}")
            if modifier_function:
                print(f"    callable: {callable(modifier_function)}")
                print(f"    type: {type(modifier_function)}")

        # Debug: Let's see what strategy name is being extracted
        print(f"\nDebug: Strategy name extraction:")
        strategy_name = engine._get_strategy_name_from_result(result_handle)
        print(f"  _get_strategy_name_from_result returned: {strategy_name}")
        print(f"  result.strategy field: {result_handle.strategy}")
        print(f"  result.match_type field: {result_handle.match_type}")

        # Debug: Let's see what base score and modifiers are being used
        print(f"\nDebug: Base score and modifiers:")
        base_score = mock_config.get_base_strategy_score(strategy_name)
        print(f"  Base score for '{strategy_name}': {base_score}")
        modifier_names = mock_config.get_all_modifier_names(strategy_name)
        print(f"  Modifier names for '{strategy_name}': {modifier_names}")

        # Debug: Let's test each modifier individually
        print(f"\nDebug: Testing individual modifiers:")
        input_text = "Farvour Turn Craft 26mm"
        for modifier_name in modifier_names:
            modifier_function = getattr(engine, f"_modifier_{modifier_name}", None)
            if modifier_function:
                modifier_value = modifier_function(input_text, result_handle, "handle_only")
                modifier_weight = mock_config.get_strategy_modifier("handle_only", modifier_name)
                effect = modifier_value * modifier_weight
                print(f"  {modifier_name}: {modifier_value} × {modifier_weight} = {effect}")

        # Expected: 40.0 + 0.0 + 0.0 + 25.0 = 65.0 (no indicators, handle brand without knot brand)
        expected_handle = 40.0 + 0.0 + 0.0 + 25.0
        print(f"handle_only: {score_handle} (expected: {expected_handle})")
        assert (
            score_handle == expected_handle
        ), f"handle_only score {score_handle} != expected {expected_handle} (penalized by knot indicators)"

        # Test knot_only strategy
        result_knot = MatchResult(
            original="Farvour Turn Craft 26mm",
            matched={"knot": {"fiber": "badger"}},
            match_type="knot_only",
            pattern="knot_only",
            strategy="knot_only",
        )

        scored_knot = engine.score_results(
            [result_knot], "Farvour Turn Craft 26mm", engine.cached_results
        )
        score_knot = scored_knot[0].score

        # Debug: Let's see what's happening with knot_only strategy
        print(f"\nDebug: knot_only strategy analysis:")
        print(f"  Final score: {score_knot}")

        # Debug: Test each modifier individually for knot_only
        print(f"\nDebug: Testing knot_only modifiers individually:")
        input_text = "Farvour Turn Craft 26mm"
        for modifier_name in mock_config.get_all_modifier_names("knot_only"):
            modifier_function = getattr(engine, f"_modifier_{modifier_name}", None)
            if modifier_function:
                modifier_value = modifier_function(input_text, result_knot, "knot_only")
                modifier_weight = mock_config.get_strategy_modifier("knot_only", modifier_name)
                effect = modifier_value * modifier_weight
                print(f"  {modifier_name}: {modifier_value} × {modifier_weight} = {effect}")

        # Debug: Test the specific brand balance modifier
        print(f"\nDebug: Testing handle_brand_without_knot_brand for knot_only:")
        brand_modifier_value = engine._modifier_handle_brand_without_knot_brand(
            input_text, result_knot, "knot_only"
        )
        brand_modifier_weight = mock_config.get_strategy_modifier(
            "knot_only", "handle_brand_without_knot_brand"
        )
        print(f"  modifier_value: {brand_modifier_value}")
        print(f"  modifier_weight: {brand_modifier_weight}")
        print(f"  expected effect: {brand_modifier_value * brand_modifier_weight}")

        # Debug: Check what the unified result contains
        print(f"\nDebug: Unified result content:")
        unified_result = engine.cached_results.get("unified_result")
        if unified_result and hasattr(unified_result, "matched"):
            handle_data = unified_result.matched.get("handle", {})
            knot_data = unified_result.matched.get("knot", {})
            print(f"  handle.brand: {handle_data.get('brand')}")
            print(f"  knot.brand: {knot_data.get('brand')}")
            print(f"  handle.model: {handle_data.get('model')}")
            print(f"  knot.fiber: {knot_data.get('fiber')}")

        # Expected: 40.0 + 0.0 + 0.0 + (-25.0) = 15.0 (no indicators, handle brand without knot brand)
        expected_knot = 40.0 + 0.0 + 0.0 + (-25.0)
        print(f"knot_only: {score_knot} (expected: {expected_knot})")
        assert (
            score_knot == expected_knot
        ), f"knot_only score {score_knot} != expected {expected_knot}"

        # Test positive case: Handle strategy with handle indicators (should get rewarded)
        print(f"\nDebug: Testing handle_only strategy with handle indicators (positive case)...")
        test_input_positive = "Farvour Turn Craft wood handle"
        result_positive = MatchResult(
            original=test_input_positive,
            matched={"handle": {"brand": "Farvour Turn Craft", "model": "Custom"}},
            match_type="handle_only",
            pattern="handle_only",
            strategy="handle_only",
        )

        scored_positive = engine.score_results(
            [result_positive], test_input_positive, engine.cached_results
        )
        score_positive = scored_positive[0].score

        # Should get higher score due to handle indicators ("wood" is a handle indicator)
        expected_positive = 40.0 + 30.0 + 25.0  # = 95.0 (rewarded by handle indicators)
        print(
            f"handle_only with handle indicators: {score_positive} (expected: {expected_positive})"
        )
        assert (
            score_positive == expected_positive
        ), f"handle_only with handle indicators should score {expected_positive}, got {score_positive}"

        # Scenario 2: Knot brand only
        print("\n=== Scenario 2: Knot brand only ===")
        # Create fresh mock_unified_result for this scenario
        mock_unified_result_scenario2 = Mock()
        mock_unified_result_scenario2.matched = {
            "handle": {"brand": "Declaration Grooming", "model": "B2"},  # Handle has brand
            "knot": {"brand": "Declaration Grooming", "model": "B2"},  # Knot has brand
        }
        engine.cached_results = {"unified_result": mock_unified_result_scenario2}

        # Test handle_only strategy with new result object for this scenario
        result_handle_scenario2 = MatchResult(
            original="Declaration B2",
            matched={"handle": {"brand": "Declaration Grooming", "model": "B2"}},
            match_type="handle_only",
            pattern="handle_only",
            strategy="handle_only",
        )

        scored_handle = engine.score_results(
            [result_handle_scenario2], "Declaration B2", engine.cached_results
        )
        score_handle = scored_handle[0].score

        # Debug: Let's see what's happening in Scenario 2
        print(f"\nDebug: Scenario 2 analysis:")
        print(f"  Input text: Declaration B2")
        print(f"  Expected score: 40.0 + 0.0 + 0.0 + 25.0 = 65.0")
        print(f"  Actual score: {score_handle}")

        # Debug: Test each modifier individually for Scenario 2
        print(f"\nDebug: Testing Scenario 2 modifiers individually:")
        input_text_scenario2 = "Declaration B2"
        for modifier_name in mock_config.get_all_modifier_names("handle_only"):
            modifier_function = getattr(engine, f"_modifier_{modifier_name}", None)
            if modifier_function:
                modifier_value = modifier_function(
                    input_text_scenario2, result_handle_scenario2, "handle_only"
                )
                modifier_weight = mock_config.get_strategy_modifier("handle_only", modifier_name)
                effect = modifier_value * modifier_weight
                print(f"  {modifier_name}: {modifier_value} × {modifier_weight} = {effect}")

        # Expected: 40.0 + 0.0 + (-30.0) + 0.0 + 0.0 = 10.0 (B2 detected as knot indicator, both have brands)
        expected_handle = 40.0 + 0.0 + (-30.0) + 0.0 + 0.0
        print(f"handle_only: {score_handle} (expected: {expected_handle})")
        assert (
            score_handle == expected_handle
        ), f"handle_only score {score_handle} != expected {expected_handle} (no indicators, both have brands)"

        # Test knot_only strategy
        scored_knot = engine.score_results([result_knot], "Declaration B2", engine.cached_results)
        score_knot = scored_knot[0].score

        # Expected: 40.0 + 0.0 + 30.0 + 0.0 + 0.0 = 70.0 (B2 detected as knot indicator, both have brands)
        expected_knot = 40.0 + 0.0 + 30.0 + 0.0 + 0.0
        print(f"knot_only: {score_knot} (expected: {expected_knot})")
        assert (
            score_knot == expected_knot
        ), f"knot_only score {score_knot} != expected {expected_knot} (B2 detected as knot indicator, both have brands)"

        # Scenario 3: Both brands
        print("\n=== Scenario 3: Both brands ===")
        mock_unified_result_scenario3 = Mock()
        mock_unified_result_scenario3.matched = {
            "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
            "knot": {"brand": "Declaration Grooming", "model": "B2"},
        }
        engine.cached_results = {"unified_result": mock_unified_result_scenario3}

        # Test handle_only strategy with new result object for this scenario
        result_handle_scenario3 = MatchResult(
            original="Farvour Turn Craft + Declaration B2",
            matched={"handle": {"brand": "Farvour Turn Craft", "model": "Custom"}},
            match_type="handle_only",
            pattern="handle_only",
            strategy="handle_only",
        )

        scored_handle = engine.score_results(
            [result_handle_scenario3], "Farvour Turn Craft + Declaration B2", engine.cached_results
        )
        score_handle = scored_handle[0].score

        # Expected: 40.0 + 0.0 + (-30.0) + 0.0 + 0.0 = 10.0 (B2 and Declaration detected as knot indicators, both have brands)
        expected_handle = 40.0 + 0.0 + (-30.0) + 0.0 + 0.0
        print(f"handle_only: {score_handle} (expected: {expected_handle})")
        assert (
            score_handle == expected_handle
        ), f"handle_only score {score_handle} != expected {expected_handle} (no indicators, both have brands)"

        # Test knot_only strategy with new result object for this scenario
        result_knot_scenario3 = MatchResult(
            original="Farvour Turn Craft + Declaration B2",
            matched={"knot": {"brand": "Declaration Grooming", "model": "B2"}},
            match_type="knot_only",
            pattern="knot_only",
            strategy="knot_only",
        )

        scored_knot = engine.score_results(
            [result_knot_scenario3], "Farvour Turn Craft + Declaration B2", engine.cached_results
        )
        score_knot = scored_knot[0].score

        # Expected: 40.0 + 0.0 + 30.0 + 0.0 + 0.0 = 70.0 (Declaration and B2 detected as knot indicators, both have brands)
        expected_knot = 40.0 + 0.0 + 30.0 + 0.0 + 0.0
        print(f"knot_only: {score_knot} (expected: {expected_knot})")
        assert (
            score_knot == expected_knot
        ), f"knot_only score {score_knot} != expected {expected_knot} (no indicators, both have brands)"

        # Scenario 4: No brands
        print("\n=== Scenario 4: No brands ===")
        mock_unified_result_scenario4 = Mock()
        mock_unified_result_scenario4.matched = {
            "handle": {"brand": None, "model": "Custom"},
            "knot": {"brand": None, "fiber": "badger"},
        }
        engine.cached_results = {"unified_result": mock_unified_result_scenario4}

        # Test handle_only strategy
        scored_handle = engine.score_results(
            [result_handle], "Custom Handle", engine.cached_results
        )
        score_handle = scored_handle[0].score

        # Expected: 40.0 + 30.0 + 0.0 = 70.0 (no brand balance modifier)
        expected_handle = 40.0 + 30.0
        print(f"handle_only: {score_handle} (expected: {expected_handle})")
        assert (
            score_handle == expected_handle
        ), f"handle_only score {score_handle} != expected {expected_handle}"

        # Test knot_only strategy
        scored_knot = engine.score_results([result_knot], "Badger Knot", engine.cached_results)
        score_knot = scored_knot[0].score

        # Expected: 40.0 + 0.0 + 0.0 = 40.0 (Badger and Knot are not specific knot model names, no brand balance modifier)
        expected_knot = 40.0 + 0.0 + 0.0
        print(f"knot_only: {score_knot} (expected: {expected_knot})")
        assert (
            score_knot == expected_knot
        ), f"knot_only score {score_knot} != expected {expected_knot} (rewarded by knot indicators, no brand balance modifier)"

        print("\n✅ All math scenarios passed!")

    def test_combined_brand_balance_modifiers(self):
        """Test both brand balance modifiers working together for handle_only strategy."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 40.0
        mock_config.get_strategy_modifier.side_effect = lambda strategy, modifier: {
            "handle_brand_without_knot_brand": 25.0,
            "knot_brand_without_handle_brand": -25.0,
        }.get(modifier, 0.0)
        mock_config.get_all_modifier_names.return_value = [
            "handle_brand_without_knot_brand",
            "knot_brand_without_handle_brand",
        ]

        engine = ScoringEngine(mock_config)

        # Mock cached_results with unified strategy results
        mock_unified_result = Mock()
        mock_unified_result.matched = {
            "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
            "knot": {"brand": None, "fiber": "badger"},
        }
        engine.cached_results = {"full_input_component_matching_result": mock_unified_result}

        result = MatchResult(
            original="Farvour Turn Craft 26mm",
            matched={
                "handle": {"brand": "Farvour Turn Craft", "model": "Custom"},
                "knot": {"brand": None, "fiber": "badger"},
            },
            match_type="handle_only",
            pattern="handle_only",
            strategy="handle_only",
        )

        scored_results = engine.score_results(
            [result], "Farvour Turn Craft 26mm", engine.cached_results
        )

        assert len(scored_results) == 1
        # Base score (40.0) + handle_brand_without_knot_brand (25.0) + knot_brand_without_handle_brand (0.0) = 65.0
        assert scored_results[0].score == 65.0


class TestPerformanceMonitor:
    """Test the PerformanceMonitor component."""

    def test_record_strategy_timing(self):
        """Test recording strategy timing."""
        monitor = PerformanceMonitor()

        monitor.record_strategy_timing("test_strategy", 0.1)
        monitor.record_strategy_timing("test_strategy", 0.2)

        stats = monitor.get_performance_stats()
        assert "test_strategy" in stats
        assert stats["test_strategy"]["count"] == 2
        assert abs(stats["test_strategy"]["total_time"] - 0.3) < 0.001

    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        monitor = PerformanceMonitor()

        # Record some timing data
        monitor.record_strategy_timing("strategy1", 0.1)
        monitor.record_strategy_timing("strategy2", 0.2)
        monitor.record_strategy_timing("strategy1", 0.15)

        stats = monitor.get_performance_stats()

        assert "strategy1" in stats
        assert "strategy2" in stats
        assert stats["strategy1"]["count"] == 2
        assert stats["strategy2"]["count"] == 1
        assert stats["strategy1"]["total_time"] == 0.25
        assert stats["strategy2"]["total_time"] == 0.2

    def test_get_performance_stats_empty(self):
        """Test getting performance stats when no data recorded."""
        monitor = PerformanceMonitor()
        stats = monitor.get_performance_stats()

        assert stats == {}

    def test_record_strategy_timing_negative_time(self):
        """Test recording negative timing (should be ignored)."""
        monitor = PerformanceMonitor()

        monitor.record_strategy_timing("test_strategy", -0.1)

        stats = monitor.get_performance_stats()
        assert "test_strategy" not in stats

    def test_performance_stats_structure(self):
        """Test that performance stats have correct structure."""
        monitor = PerformanceMonitor()

        monitor.record_strategy_timing("test_strategy", 0.1)
        stats = monitor.get_performance_stats()

        strategy_stats = stats["test_strategy"]
        assert "count" in strategy_stats
        assert "total_time" in strategy_stats
        assert "average_time" in strategy_stats
        assert "min_time" in strategy_stats
        assert "max_time" in strategy_stats

        assert strategy_stats["count"] == 1
        assert strategy_stats["total_time"] == 0.1
        assert strategy_stats["average_time"] == 0.1
        assert strategy_stats["min_time"] == 0.1
        assert strategy_stats["max_time"] == 0.1
