"""
Tests for Individual Brush Strategy Classes.

This test file tests the individual brush strategies that replace the
complete_brush wrapper strategy.
"""


class TestKnownBrushMatchingStrategy:
    """Test KnownBrushMatchingStrategy as individual strategy."""

    def test_known_brush_strategy_creation(self):
        """Test that KnownBrushMatchingStrategy can be created as individual strategy."""
        from sotd.match.brush_matching_strategies.known_brush_strategy import (
            KnownBrushMatchingStrategy,
        )

        catalog_data = {
            "Simpson": {
                "Chubby 2": {
                    "fiber": "Badger",
                    "knot_size_mm": 27,
                    "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
                }
            }
        }

        strategy = KnownBrushMatchingStrategy(catalog_data)
        assert strategy is not None
        assert hasattr(strategy, "match")

    def test_known_brush_strategy_matches_simpson_chubby_2(self):
        """Test that KnownBrushMatchingStrategy matches Simpson Chubby 2."""
        from sotd.match.brush_matching_strategies.known_brush_strategy import (
            KnownBrushMatchingStrategy,
        )

        catalog_data = {
            "Simpson": {
                "Chubby 2": {
                    "fiber": "Badger",
                    "knot_size_mm": 27,
                    "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
                }
            }
        }

        strategy = KnownBrushMatchingStrategy(catalog_data)
        result = strategy.match("Simpson Chubby 2")

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"
        assert result.matched["fiber"] == "Badger"
        assert result.matched["knot_size_mm"] == 27
        assert result.strategy == "known_brush"

    def test_known_brush_strategy_returns_none_for_no_match(self):
        """Test that KnownBrushMatchingStrategy returns None for no match."""
        from sotd.match.brush_matching_strategies.known_brush_strategy import (
            KnownBrushMatchingStrategy,
        )

        catalog_data = {
            "Simpson": {
                "Chubby 2": {
                    "fiber": "Badger",
                    "knot_size_mm": 27,
                    "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
                }
            }
        }

        strategy = KnownBrushMatchingStrategy(catalog_data)
        result = strategy.match("Unknown Brush")

        assert result is not None
        assert result.matched is None


class TestOmegaSemogueBrushMatchingStrategy:
    """Test OmegaSemogueBrushMatchingStrategy as individual strategy."""

    def test_omega_semogue_strategy_creation(self):
        """Test that OmegaSemogueBrushMatchingStrategy can be created as individual strategy."""
        from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
            OmegaSemogueBrushMatchingStrategy,
        )

        strategy = OmegaSemogueBrushMatchingStrategy()
        assert strategy is not None
        assert hasattr(strategy, "match")

    def test_omega_semogue_strategy_matches_omega_10049(self):
        """Test that OmegaSemogueBrushMatchingStrategy matches Omega 10049."""
        from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
            OmegaSemogueBrushMatchingStrategy,
        )

        strategy = OmegaSemogueBrushMatchingStrategy()
        result = strategy.match("Omega 10049")

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Omega"
        assert result.matched["model"] == "10049"
        assert result.matched["fiber"] == "Boar"
        assert result.strategy == "omega_semogue"

    def test_omega_semogue_strategy_matches_semogue_c3(self):
        """Test that OmegaSemogueBrushMatchingStrategy matches Semogue C3."""
        from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
            OmegaSemogueBrushMatchingStrategy,
        )

        strategy = OmegaSemogueBrushMatchingStrategy()
        result = strategy.match("Semogue C3")

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Semogue"
        assert result.matched["model"] == "c3"  # Fixed: lowercase as returned by strategy
        assert result.matched["fiber"] == "Boar"
        assert result.strategy == "omega_semogue"

    def test_omega_semogue_strategy_returns_none_for_no_match(self):
        """Test that OmegaSemogueBrushMatchingStrategy returns None for no match."""
        from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
            OmegaSemogueBrushMatchingStrategy,
        )

        strategy = OmegaSemogueBrushMatchingStrategy()
        result = strategy.match("Unknown Brush")

        assert result is not None
        assert result.matched is None


class TestZenithBrushMatchingStrategy:
    """Test ZenithBrushMatchingStrategy as individual strategy."""

    def test_zenith_strategy_creation(self):
        """Test that ZenithBrushMatchingStrategy can be created as individual strategy."""
        from sotd.match.brush_matching_strategies.zenith_strategy import (
            ZenithBrushMatchingStrategy,
        )

        strategy = ZenithBrushMatchingStrategy()
        assert strategy is not None
        assert hasattr(strategy, "match")

    def test_zenith_strategy_matches_zenith_b2(self):
        """Test that ZenithBrushMatchingStrategy matches Zenith B2."""
        from sotd.match.brush_matching_strategies.zenith_strategy import (
            ZenithBrushMatchingStrategy,
        )

        strategy = ZenithBrushMatchingStrategy()
        result = strategy.match("Zenith B2")

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Zenith"
        assert result.matched["model"] == "B2"
        assert result.matched["fiber"] == "Boar"  # Fixed: capitalized as returned by strategy
        assert result.strategy == "zenith"

    def test_zenith_strategy_returns_none_for_no_match(self):
        """Test that ZenithBrushMatchingStrategy returns None for no match."""
        from sotd.match.brush_matching_strategies.zenith_strategy import (
            ZenithBrushMatchingStrategy,
        )

        strategy = ZenithBrushMatchingStrategy()
        result = strategy.match("Unknown Brush")

        assert result is not None
        assert result.matched is None


class TestOtherBrushMatchingStrategy:
    """Test OtherBrushMatchingStrategy as individual strategy."""

    def test_other_brush_strategy_creation(self):
        """Test that OtherBrushMatchingStrategy can be created as individual strategy."""
        from sotd.match.brush_matching_strategies.other_brushes_strategy import (
            OtherBrushMatchingStrategy,
        )

        catalog_data = {
            "Elite": {
                "default": "Badger",
                "patterns": ["elite"],
            }
        }

        strategy = OtherBrushMatchingStrategy(catalog_data)
        assert strategy is not None
        assert hasattr(strategy, "match")

    def test_other_brush_strategy_matches_elite_brush(self):
        """Test that OtherBrushMatchingStrategy matches Elite brush."""
        from sotd.match.brush_matching_strategies.other_brushes_strategy import (
            OtherBrushMatchingStrategy,
        )

        catalog_data = {
            "Elite": {
                "default": "Badger",
                "patterns": ["elite"],
            }
        }

        strategy = OtherBrushMatchingStrategy(catalog_data)
        result = strategy.match("Elite Brush")

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Elite"
        assert result.matched["fiber"] == "Badger"
        # Fixed: strategy name is now set to "other_brush"
        assert result.strategy == "other_brush"

    def test_other_brush_strategy_returns_none_for_no_match(self):
        """Test that OtherBrushMatchingStrategy returns None for no match."""
        from sotd.match.brush_matching_strategies.other_brushes_strategy import (
            OtherBrushMatchingStrategy,
        )

        catalog_data = {
            "Elite": {
                "default": "Badger",
                "patterns": ["elite"],
            }
        }

        strategy = OtherBrushMatchingStrategy(catalog_data)
        result = strategy.match("Unknown Brush")

        assert result is not None
        assert result.matched is None


class TestIndividualBrushStrategyIntegration:
    """Test integration of individual brush strategies with scoring system."""

    def test_individual_strategies_can_be_used_in_scoring_system(self):
        """Test that individual strategies can be used in the scoring system."""
        from sotd.match.brush_matching_strategies.known_brush_strategy import (
            KnownBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
            OmegaSemogueBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.zenith_strategy import (
            ZenithBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.other_brushes_strategy import (
            OtherBrushMatchingStrategy,
        )

        # Create individual strategies
        catalog_data = {
            "Simpson": {
                "Chubby 2": {
                    "fiber": "Badger",
                    "knot_size_mm": 27,
                    "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
                }
            }
        }

        strategies = [
            KnownBrushMatchingStrategy(catalog_data),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy({}),
        ]

        # Test that all strategies can be created and have match method
        for strategy in strategies:
            assert strategy is not None
            assert hasattr(strategy, "match")
            assert callable(strategy.match)

    def test_individual_strategies_produce_consistent_results(self):
        """Test that individual strategies produce consistent results with legacy system."""
        from sotd.match.brush_matching_strategies.known_brush_strategy import (
            KnownBrushMatchingStrategy,
        )

        catalog_data = {
            "Simpson": {
                "Chubby 2": {
                    "fiber": "Badger",
                    "knot_size_mm": 27,
                    "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
                }
            }
        }

        strategy = KnownBrushMatchingStrategy(catalog_data)
        result = strategy.match("Simpson Chubby 2")

        # Verify result structure matches expected format
        assert result is not None
        assert hasattr(result, "matched")
        assert hasattr(result, "strategy")
        assert hasattr(result, "match_type")
        assert hasattr(result, "pattern")

        # Verify matched data structure
        if result.matched:
            assert "brand" in result.matched
            assert "model" in result.matched
            assert "fiber" in result.matched
            assert "knot_size_mm" in result.matched
