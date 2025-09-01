"""
Detailed performance profiling for SOTD Pipeline match phase.

This test profiles individual components to identify performance bottlenecks
beyond the O(1) correct matches lookup optimization.
"""

import time

from sotd.match.razor_matcher import RazorMatcher
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.utils.extract_normalization import normalize_for_matching


class TestDetailedPerformanceProfiling:
    """Detailed performance profiling for match phase components."""

    def test_normalize_for_matching_performance(self):
        """Profile the normalize_for_matching function performance."""
        test_cases = [
            "Feather",
            "Gillette Silver Blue",
            "Personna Hair Shaper",
            "Barrister and Mann Seville",
            "Simpson Chubby 2 Manchurian",
        ]

        print("\n=== normalize_for_matching Performance ===")

        # Test each field type
        for field in ["blade", "razor", "soap", "brush"]:
            start_time = time.time()
            for _ in range(100):
                for test_case in test_cases:
                    normalize_for_matching(test_case, field=field)
            elapsed = time.time() - start_time

            avg_time = elapsed / (100 * len(test_cases))
            print(f"{field.capitalize()} normalization: {avg_time:.6f}s per call")

    def test_blade_matcher_components(self):
        """Profile individual BladeMatcher components."""
        matcher = BladeMatcher()
        test_case = "Feather"

        print("\n=== BladeMatcher Component Performance ===")

        # Test normalize_for_matching call
        start_time = time.time()
        for _ in range(100):
            normalize_for_matching(test_case, field="blade")
        elapsed = time.time() - start_time
        print(f"normalize_for_matching: {elapsed/100:.6f}s per call")

        # Test _collect_all_correct_matches
        start_time = time.time()
        for _ in range(100):
            matcher._collect_all_correct_matches(test_case)
        elapsed = time.time() - start_time
        print(f"_collect_all_correct_matches: {elapsed/100:.6f}s per call")

        # Test case-insensitive lookup building
        matcher.clear_cache()  # Force rebuild
        start_time = time.time()
        lookup = matcher._build_case_insensitive_lookup()
        elapsed = time.time() - start_time
        print(f"Case-insensitive lookup build: {elapsed:.6f}s (one-time)")
        print(f"Lookup dictionary size: {len(lookup)} entries")

    def test_razor_matcher_components(self):
        """Profile individual RazorMatcher components."""
        matcher = RazorMatcher()
        test_case = "Gillette Superspeed"

        print("\n=== RazorMatcher Component Performance ===")

        # Test _check_correct_matches
        start_time = time.time()
        for _ in range(100):
            matcher._check_correct_matches(test_case)
        elapsed = time.time() - start_time
        print(f"_check_correct_matches: {elapsed/100:.6f}s per call")

        # Test case-insensitive lookup building
        matcher.clear_cache()  # Force rebuild
        start_time = time.time()
        lookup = matcher._build_case_insensitive_lookup()
        elapsed = time.time() - start_time
        print(f"Case-insensitive lookup build: {elapsed:.6f}s (one-time)")
        print(f"Lookup dictionary size: {len(lookup)} entries")

    def test_soap_matcher_components(self):
        """Profile individual SoapMatcher components."""
        matcher = SoapMatcher()
        test_case = "Barrister and Mann Seville"

        print("\n=== SoapMatcher Component Performance ===")

        # Test _check_correct_matches
        start_time = time.time()
        for _ in range(100):
            matcher._check_correct_matches(test_case)
        elapsed = time.time() - start_time
        print(f"_check_correct_matches: {elapsed/100:.6f}s per call")

        # Test case-insensitive lookup building
        matcher.clear_cache()  # Force rebuild
        start_time = time.time()
        lookup = matcher._build_case_insensitive_lookup()
        elapsed = time.time() - start_time
        print(f"Case-insensitive lookup build: {elapsed:.6f}s (one-time)")
        print(f"Lookup dictionary size: {len(lookup)} entries")

    def test_brush_matcher_components(self):
        """Profile individual BrushMatcher components."""
        matcher = BrushMatcher()
        test_case = "simpson chubby 2 manchurian"

        print("\n=== BrushMatcher Component Performance ===")

        # Test full match() method
        start_time = time.time()
        for _ in range(100):
            matcher.match(test_case)
        elapsed = time.time() - start_time
        print(f"Full match() method: {elapsed/100:.6f}s per call")

        # Test correct matches strategy specifically
        # Note: BrushMatcher uses internal strategy orchestrator, not direct strategy access

    def test_correct_matches_data_sizes(self):
        """Compare correct matches data sizes across matchers."""
        print("\n=== Correct Matches Data Sizes ===")

        matchers = {
            "razor": RazorMatcher(),
            "blade": BladeMatcher(),
            "soap": SoapMatcher(),
            "brush": BrushMatcher(),
        }

        for field_type, matcher in matchers.items():
            if hasattr(matcher, "correct_matches"):
                size = len(str(matcher.correct_matches))
                print(f"{field_type.capitalize()}Matcher correct_matches size: {size:,} characters")

            if hasattr(matcher, "_normalized_correct_matches"):
                size = len(matcher._normalized_correct_matches)
                print(f"{field_type.capitalize()}Matcher normalized entries: {size:,}")

    def test_pattern_compilation_performance(self):
        """Profile pattern compilation performance."""
        print("\n=== Pattern Compilation Performance ===")

        matchers = {
            "razor": RazorMatcher(),
            "blade": BladeMatcher(),
            "soap": SoapMatcher(),
        }

        for field_type, matcher in matchers.items():
            if hasattr(matcher, "patterns"):
                pattern_count = len(matcher.patterns)
                print(
                    f"{field_type.capitalize()}Matcher patterns: {pattern_count:,} compiled patterns"
                )

    def test_memory_usage_comparison(self):
        """Compare memory usage of different matchers."""
        import sys

        print("\n=== Memory Usage Comparison ===")

        matchers = {
            "razor": RazorMatcher(),
            "blade": BladeMatcher(),
            "soap": SoapMatcher(),
            "brush": BrushMatcher(),
        }

        for field_type, matcher in matchers.items():
            size = sys.getsizeof(matcher)
            print(f"{field_type.capitalize()}Matcher memory: {size:,} bytes")

    def test_comprehensive_performance_analysis(self):
        """Run comprehensive performance analysis."""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE PERFORMANCE ANALYSIS")
        print("=" * 60)

        # Run all profiling tests
        self.test_normalize_for_matching_performance()
        self.test_blade_matcher_components()
        self.test_razor_matcher_components()
        self.test_soap_matcher_components()
        self.test_brush_matcher_components()
        self.test_correct_matches_data_sizes()
        self.test_pattern_compilation_performance()
        self.test_memory_usage_comparison()

        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
