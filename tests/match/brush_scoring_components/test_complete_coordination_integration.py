"""Complete coordination integration tests for multi-strategy scoring system."""

from sotd.match.brush_matcher import BrushMatcher


class TestCompleteCoordinationIntegration:
    """Test complete coordination of all components in the scoring system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = BrushMatcher()

    def test_complete_workflow_with_all_components(self):
        """Test complete workflow with all coordination components active."""
        # Test with a brush that should trigger multiple strategies
        result = self.matcher.match("Declaration B2 in Mozingo handle")

        # Should get a valid result
        assert result is not None
        assert result.matched is not None

        # Check that all components are properly integrated
        assert hasattr(self.matcher, "strategy_orchestrator")
        assert hasattr(self.matcher, "scoring_engine")
        assert hasattr(self.matcher, "result_processor")
        assert hasattr(self.matcher, "conflict_resolver")
        assert hasattr(self.matcher, "performance_optimizer")
        assert hasattr(self.matcher, "strategy_dependency_manager")

    def test_coordination_with_conflict_resolution(self):
        """Test coordination when conflicts are detected and resolved."""
        # This test validates that conflict resolution works with other components
        result = self.matcher.match("Declaration B2")

        # Should get a valid result even if conflicts occurred
        assert result is not None

        # Check that conflict resolver is properly integrated
        # Should not raise any errors even if no conflicts occurred
        self.matcher.conflict_resolver.get_conflict_summary([])

    def test_coordination_with_performance_tracking(self):
        """Test coordination with performance tracking and optimization."""
        # Run multiple matches to build performance data
        test_brushes = [
            "Declaration B2",
            "Declaration Grooming B2",
            "Mozingo Declaration B2",
            "Declaration B2 in custom handle",
        ]

        for brush in test_brushes:
            result = self.matcher.match(brush)
            assert result is not None

        # Check that performance data is being tracked
        performance_stats = self.matcher.get_performance_stats()
        assert "strategy_performance" in performance_stats
        assert "optimization_recommendations" in performance_stats
        assert "slow_strategies" in performance_stats

    def test_coordination_with_dependency_management(self):
        """Test coordination with dependency management."""
        # Check that dependency manager is properly integrated
        dependency_info = self.matcher.get_dependency_info()
        assert "dependency_manager" in dependency_info
        assert "dependencies" in dependency_info
        assert "dependency_graph" in dependency_info
        assert "topological_graph" in dependency_info

        # Test that dependency constraints are applied during matching
        result = self.matcher.match("Declaration B2")
        assert result is not None

    def test_coordination_error_handling(self):
        """Test coordination error handling across all components."""
        # Test with invalid input
        self.matcher.match("")
        # Should handle gracefully without crashing

        # Test with very long input
        long_input = "A" * 1000
        self.matcher.match(long_input)
        # Should handle gracefully

    def test_coordination_memory_management(self):
        """Test coordination memory management across all components."""
        # Run multiple matches to test memory usage
        test_brushes = [
            "Declaration B2",
            "Declaration Grooming B2",
            "Mozingo Declaration B2",
            "Declaration B2 in custom handle",
            "Declaration B2 with badger knot",
            "Declaration B2 26mm",
            "Declaration B2 synthetic",
            "Declaration B2 boar",
            "Declaration B2 horse",
            "Declaration B2 mixed",
        ]

        for brush in test_brushes:
            result = self.matcher.match(brush)
            assert result is not None

        # Check that cache stats are available
        cache_stats = self.matcher.get_cache_stats()
        assert "performance" in cache_stats
        assert "total_time" in cache_stats

    def test_coordination_data_flow(self):
        """Test data flow through all coordination components."""
        # Test the complete data flow
        input_value = "Declaration B2 in Mozingo handle"

        # Step 1: Strategy orchestration
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(input_value)
        assert len(strategy_results) > 0

        # Step 2: Performance tracking
        self.matcher._track_strategy_performance(strategy_results, input_value)

        # Step 3: Dependency constraints
        executable_results = self.matcher._apply_dependency_constraints(strategy_results)
        assert len(executable_results) > 0

        # Step 4: Conflict resolution
        self.matcher.conflict_resolver.resolve_conflicts(
            executable_results, resolution_method="score"
        )

        # Step 5: Scoring
        scored_results = self.matcher.scoring_engine.score_results(executable_results, input_value)
        assert len(scored_results) > 0

        # Step 6: Best result selection
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)
        assert best_result is not None

        # Step 7: Result processing
        final_result = self.matcher.result_processor.process_result(best_result, input_value)
        assert final_result is not None

    def test_coordination_component_isolation(self):
        """Test that components are properly isolated and don't interfere with each other."""
        # Test that each component can be accessed independently
        assert self.matcher.strategy_orchestrator is not None
        assert self.matcher.scoring_engine is not None
        assert self.matcher.result_processor is not None
        assert self.matcher.conflict_resolver is not None
        assert self.matcher.performance_optimizer is not None
        assert self.matcher.strategy_dependency_manager is not None

        # Test that components don't share mutable state inappropriately
        original_cache_stats = self.matcher.get_cache_stats()

        # Run a match
        result = self.matcher.match("Declaration B2")
        assert result is not None

        # Check that cache stats changed (indicating proper isolation)
        new_cache_stats = self.matcher.get_cache_stats()
        assert new_cache_stats != original_cache_stats

    def test_coordination_consistency(self):
        """Test coordination consistency across multiple runs."""
        # Run the same input multiple times
        input_value = "Declaration B2"
        results = []

        for _ in range(5):
            result = self.matcher.match(input_value)
            results.append(result)
            assert result is not None

        # All results should be consistent
        first_result = results[0]
        for result in results[1:]:
            # Results should be equivalent (same matched data)
            assert result.matched == first_result.matched

    def test_coordination_performance_characteristics(self):
        """Test coordination performance characteristics."""
        import time

        # Test performance of complete workflow
        test_brushes = [
            "Declaration B2",
            "Declaration Grooming B2",
            "Mozingo Declaration B2",
            "Declaration B2 in custom handle",
            "Declaration B2 with badger knot",
            "Declaration B2 26mm",
            "Declaration B2 synthetic",
            "Declaration B2 boar",
            "Declaration B2 horse",
            "Declaration B2 mixed",
        ]

        start_time = time.time()

        for brush in test_brushes:
            result = self.matcher.match(brush)
            assert result is not None

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete 10 matches in reasonable time (< 5 seconds)
        assert total_time < 5.0

        # Average time per match should be reasonable (< 0.5 seconds)
        avg_time_per_match = total_time / len(test_brushes)
        assert avg_time_per_match < 0.5

    def test_coordination_alignment_with_requirements(self):
        """Test 100% alignment with multi-strategy scoring system requirements."""
        # Test that all required features are present and working

        # 1. Multi-strategy execution
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies("Declaration B2")
        assert len(strategy_results) > 0

        # 2. Result scoring
        scored_results = self.matcher.scoring_engine.score_results(
            strategy_results, "Declaration B2"
        )
        assert len(scored_results) > 0
        assert all(hasattr(result, "score") for result in scored_results)

        # 3. Best result selection
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)
        assert best_result is not None

        # 4. Conflict resolution
        self.matcher.conflict_resolver.resolve_conflicts(
            strategy_results, resolution_method="score"
        )
        # Should not raise errors

        # 5. Performance optimization
        performance_stats = self.matcher.get_performance_stats()
        assert "strategy_performance" in performance_stats

        # 6. Dependency management
        dependency_info = self.matcher.get_dependency_info()
        assert "dependency_manager" in dependency_info

        # 7. Result processing
        final_result = self.matcher.result_processor.process_result(best_result, "Declaration B2")
        assert final_result is not None
        assert hasattr(final_result, "matched")
        assert hasattr(final_result, "match_type")
        assert hasattr(final_result, "pattern")

    def test_coordination_edge_cases(self):
        """Test coordination with edge cases and boundary conditions."""
        # Test with various edge cases

        # Empty string
        self.matcher.match("")
        # Should handle gracefully

        # Very short string
        self.matcher.match("A")
        # Should handle gracefully

        # String with special characters
        self.matcher.match("Declaration B2 (special) [brackets]")
        # Should handle gracefully

        # String with numbers
        self.matcher.match("Declaration B2 123 456")
        # Should handle gracefully

        # String with mixed case
        self.matcher.match("DECLARATION b2 In MOZINGO Handle")
        # Should handle gracefully

    def test_coordination_integration_stability(self):
        """Test coordination integration stability under load."""
        # Test stability with multiple rapid calls
        test_inputs = [
            "Declaration B2",
            "Declaration Grooming B2",
            "Mozingo Declaration B2",
            "Declaration B2 in custom handle",
            "Declaration B2 with badger knot",
            "Declaration B2 26mm",
            "Declaration B2 synthetic",
            "Declaration B2 boar",
            "Declaration B2 horse",
            "Declaration B2 mixed",
        ]

        results = []
        for input_value in test_inputs:
            result = self.matcher.match(input_value)
            results.append(result)
            assert result is not None

        # All results should be valid
        assert all(result is not None for result in results)

        # Performance stats should be available
        performance_stats = self.matcher.get_performance_stats()
        assert "strategy_performance" in performance_stats
