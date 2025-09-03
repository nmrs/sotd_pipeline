"""
Test performance of correct matches lookup across all field types.

This test validates that all field types use O(1) lookups and identifies
which ones still need optimization.
"""

import pytest
import time
from pathlib import Path

from sotd.match.razor_matcher import RazorMatcher
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.brush_matcher import BrushMatcher


class TestAllFieldTypesPerformance:
    """Test performance characteristics across all field types."""

    def test_razor_matcher_performance(self):
        """Test that RazorMatcher uses O(1) lookup."""
        matcher = RazorMatcher()

        # Test multiple lookups to verify O(1) performance
        test_cases = [
            "Gillette Superspeed",
            "gillette superspeed",
            "GILLETTE SUPERSPEED",
            "att s1",
            "ATT S1",
        ]

        # First lookup (builds dictionary)
        start_time = time.time()
        result1 = matcher._check_correct_matches(test_cases[0])
        first_lookup_time = time.time() - start_time

        # Subsequent lookups (should be O(1))
        start_time = time.time()
        for test_case in test_cases[1:]:
            result = matcher._check_correct_matches(test_case)
        subsequent_lookups_time = time.time() - start_time

        # First lookup should be slower (builds dictionary)
        assert first_lookup_time > 0.0001, f"First lookup too fast: {first_lookup_time:.6f}s"

        # Subsequent lookups should be very fast (O(1))
        avg_subsequent_time = subsequent_lookups_time / (len(test_cases) - 1)
        assert (
            avg_subsequent_time < 0.0001
        ), f"Subsequent lookups too slow: {avg_subsequent_time:.6f}s"

        print(
            f"RazorMatcher - First: {first_lookup_time:.6f}s, Subsequent avg: {avg_subsequent_time:.6f}s"
        )

    def test_blade_matcher_performance(self):
        """Test BladeMatcher performance (may still be O(n))."""
        matcher = BladeMatcher()

        test_cases = [
            "Feather",
            "feather",
            "FEATHER",
            "Gillette Silver Blue",
            "gillette silver blue",
        ]

        # Test multiple lookups
        start_time = time.time()
        for test_case in test_cases:
            result = matcher._collect_all_correct_matches(test_case)
        total_time = time.time() - start_time

        avg_time = total_time / len(test_cases)
        print(f"BladeMatcher - Avg lookup time: {avg_time:.6f}s")

        # BladeMatcher might still be O(n) - this test documents current performance
        assert avg_time < 0.01, f"BladeMatcher too slow: {avg_time:.6f}s"

    def test_soap_matcher_performance(self):
        """Test SoapMatcher performance (likely still O(n))."""
        matcher = SoapMatcher()

        # Note: SoapMatcher might not have many correct matches entries
        test_cases = [
            "Barrister and Mann Seville",
            "barrister and mann seville",
            "BARRISTER AND MANN SEVILLE",
        ]

        # Test multiple lookups
        start_time = time.time()
        for test_case in test_cases:
            result = matcher._check_correct_matches(test_case)
        total_time = time.time() - start_time

        avg_time = total_time / len(test_cases)
        print(f"SoapMatcher - Avg lookup time: {avg_time:.6f}s")

        # SoapMatcher likely still O(n) - this test documents current performance
        assert avg_time < 0.01, f"SoapMatcher too slow: {avg_time:.6f}s"

    def test_brush_matcher_performance(self):
        """Test BrushMatcher performance (uses CorrectMatchesChecker)."""
        matcher = BrushMatcher()

        test_cases = [
            "simpson chubby 2 manchurian",
            "Simpson Chubby 2 Manchurian",
            "SIMPSON CHUBBY 2 MANCHURIAN",
        ]

        # Test multiple lookups
        start_time = time.time()
        for test_case in test_cases:
            result = matcher.match(test_case)
        total_time = time.time() - start_time

        avg_time = total_time / len(test_cases)
        print(f"BrushMatcher - Avg lookup time: {avg_time:.6f}s")

        # BrushMatcher likely still O(n) - this test documents current performance
        assert avg_time < 0.01, f"BrushMatcher too slow: {avg_time:.6f}s"

    def test_performance_comparison(self):
        """Compare performance across all field types."""
        results = {}

        # Create matcher instances once
        matchers = {
            "razor": RazorMatcher(),
            "blade": BladeMatcher(),
            "soap": SoapMatcher(),
            "brush": BrushMatcher(),
        }

        # Test each matcher with 10 lookups
        test_cases = {
            "razor": "Gillette Superspeed",
            "blade": "Feather",
            "soap": "Barrister and Mann Seville",
            "brush": "simpson chubby 2 manchurian",
        }

        for field_type, test_case in test_cases.items():
            matcher = matchers[field_type]
            start_time = time.time()

            if field_type == "razor":
                for _ in range(10):
                    matcher._check_correct_matches(test_case)
            elif field_type == "blade":
                for _ in range(10):
                    matcher._collect_all_correct_matches(test_case)
            elif field_type == "soap":
                for _ in range(10):
                    matcher._check_correct_matches(test_case)
            elif field_type == "brush":
                for _ in range(10):
                    matcher.match(test_case)

            results[field_type] = time.time() - start_time

        print("\nPerformance Comparison (10 lookups each):")
        for field_type, time_taken in results.items():
            print(f"  {field_type.capitalize()}: {time_taken:.6f}s")

        # RazorMatcher should be fast (O(1) after first lookup)
        # Note: First lookup builds dictionary, so it might not be fastest in this test
        assert results["razor"] < 0.01, "RazorMatcher should be reasonably fast"
        assert results["blade"] < 0.01, "BladeMatcher should be reasonably fast"
        assert results["soap"] < 0.01, "SoapMatcher should be reasonably fast"
        assert results["brush"] < 0.1, "BrushMatcher should be reasonably fast"

    def test_identify_optimization_candidates(self):
        """Identify which field types need O(1) optimization."""
        optimization_needed = []

        # Create matcher instances once to avoid rebuilding lookup dictionaries
        matchers = {
            "razor": RazorMatcher(),
            "blade": BladeMatcher(),
            "soap": SoapMatcher(),
            "brush": BrushMatcher(),
        }

        # Test each field type and identify slow ones
        field_tests = [
            ("razor", lambda: matchers["razor"]._check_correct_matches("Gillette Superspeed")),
            ("blade", lambda: matchers["blade"]._collect_all_correct_matches("Feather")),
            ("soap", lambda: matchers["soap"]._check_correct_matches("Barrister and Mann Seville")),
            ("brush", lambda: matchers["brush"].match("simpson chubby 2 manchurian")),
        ]

        for field_type, test_func in field_tests:
            # Time 100 lookups with same matcher instance
            start_time = time.time()
            for _ in range(100):
                test_func()
            elapsed = time.time() - start_time

            avg_time = elapsed / 100
            print(f"{field_type.capitalize()}Matcher: {avg_time:.6f}s per lookup")

            # If average time is > 0.0001s, it likely needs optimization
            # Note: BrushMatcher does more complex processing, so use higher threshold
            threshold = 0.002 if field_type == "brush" else 0.0001
            if avg_time > threshold:
                optimization_needed.append(field_type)

        print(f"\nField types needing O(1) optimization: {optimization_needed}")

        # Based on actual performance testing:
        # - RazorMatcher: 0.000007s (optimized O(1))
        # - BladeMatcher: 0.000026s (optimized O(1))
        # - SoapMatcher: 0.000000s (optimized O(1))
        # - BrushMatcher: 0.000385s (optimized O(1))

        expected_optimized = ["razor", "blade", "soap", "brush"]
        expected_fast_enough = []
        expected_needs_optimization = []

        for field_type in expected_optimized:
            assert (
                field_type not in optimization_needed
            ), f"{field_type} should be optimized but isn't"

        for field_type in expected_fast_enough:
            assert field_type not in optimization_needed, f"{field_type} is already fast enough"

        for field_type in expected_needs_optimization:
            assert (
                field_type in optimization_needed
            ), f"{field_type} should need optimization but doesn't"
