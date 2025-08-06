"""
Integration tests for BrushMatcherEntryPoint.

Tests the entry point with real data and pipeline integration.
"""

import pytest
from pathlib import Path

from sotd.match.brush_matcher_entry import BrushMatcherEntryPoint


class TestBrushMatcherEntryPointIntegration:
    """Integration tests for BrushMatcherEntryPoint."""

    def test_entry_point_with_real_brush_data(self):
        """Test entry point with real brush data from production."""
        # Test with a known brush that should match
        test_brush = "Simpson Chubby 2"

        # Test old system
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
        result_old = entry_point_old.match(test_brush)

        # Test new system
        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        result_new = entry_point_new.match(test_brush)

        # Both systems should produce compatible results
        assert result_old is not None
        assert result_new is not None
        assert result_old.original == result_new.original
        assert result_old.match_type == result_new.match_type
        assert result_old.matched is not None
        assert result_new.matched is not None
        assert result_old.matched.get("brand") == result_new.matched.get("brand")
        assert result_old.matched.get("model") == result_new.matched.get("model")

    def test_entry_point_with_complex_brush_data(self):
        """Test entry point with complex brush data (handle/knot combinations)."""
        # Test with a complex brush that requires splitting
        test_brush = "Chisel & Hound 'The Duke' / Omega 10098 Boar"

        # Test old system
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
        result_old = entry_point_old.match(test_brush)

        # Test new system
        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        result_new = entry_point_new.match(test_brush)

        # Both systems should produce compatible results
        assert result_old is not None
        assert result_new is not None
        assert result_old.original == result_new.original
        assert result_old.match_type == result_new.match_type

    def test_entry_point_with_unmatched_brush_data(self):
        """Test entry point with unmatched brush data."""
        # Test with an unmatched brush
        test_brush = "Unknown Brush Brand XYZ123"

        # Test old system
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
        result_old = entry_point_old.match(test_brush)

        # Test new system
        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        result_new = entry_point_new.match(test_brush)

        # Both systems should handle unmatched data consistently
        if result_old is None:
            assert result_new is None
        else:
            assert result_new is not None
            assert result_old.original == result_new.original

    def test_entry_point_cache_stats(self):
        """Test that both systems provide cache statistics."""
        # Test old system
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
        stats_old = entry_point_old.get_cache_stats()

        # Test new system
        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        stats_new = entry_point_new.get_cache_stats()

        # Both should return dictionary with cache stats
        assert isinstance(stats_old, dict)
        assert isinstance(stats_new, dict)
        assert "hits" in stats_old or "misses" in stats_old
        assert "hits" in stats_new or "misses" in stats_new

    def test_entry_point_system_identification(self):
        """Test that entry point correctly identifies active system."""
        # Test old system
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
        assert entry_point_old.get_system_name() == "legacy"

        # Test new system
        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        assert entry_point_new.get_system_name() == "scoring"

    def test_entry_point_with_pipeline_configuration(self):
        """Test entry point with typical pipeline configuration."""
        # Simulate typical pipeline configuration
        config = {
            "catalog_path": Path("data/brushes.yaml"),
            "handles_path": Path("data/handles.yaml"),
            "knots_path": Path("data/knots.yaml"),
            "correct_matches_path": Path("data/correct_matches.yaml"),
            "debug": False,
        }

        # Test old system with configuration
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False, **config)
        result_old = entry_point_old.match("Simpson Chubby 2")

        # Test new system with configuration
        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True, **config)
        result_new = entry_point_new.match("Simpson Chubby 2")

        # Both should work with pipeline configuration
        assert result_old is not None
        assert result_new is not None

    def test_entry_point_performance_comparison(self):
        """Test that both systems have similar performance characteristics."""
        import time

        test_brush = "Simpson Chubby 2"

        # Test old system performance
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
        start_time = time.time()
        result_old = entry_point_old.match(test_brush)
        old_time = time.time() - start_time

        # Test new system performance
        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        start_time = time.time()
        result_new = entry_point_new.match(test_brush)
        new_time = time.time() - start_time

        # Both should complete in reasonable time
        assert old_time < 1.0  # Should complete in under 1 second
        assert new_time < 1.0  # Should complete in under 1 second

        # Results should be compatible
        assert result_old is not None
        assert result_new is not None
        assert result_old.matched is not None
        assert result_new.matched is not None
        assert result_old.matched.get("brand") == result_new.matched.get("brand")

    def test_entry_point_error_handling(self):
        """Test that both systems handle errors gracefully."""
        # Test with empty string
        entry_point_old = BrushMatcherEntryPoint(use_scoring_system=False)
        result_old = entry_point_old.match("")

        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        result_new = entry_point_new.match("")

        # Both should handle empty input gracefully
        assert result_old is None
        assert result_new is None

        # Test with None input
        result_old = entry_point_old.match(None)  # type: ignore
        result_new = entry_point_new.match(None)  # type: ignore

        # Both should handle None input gracefully
        assert result_old is None
        assert result_new is None
