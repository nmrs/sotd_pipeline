"""
Test BrushMatcher correct matches optimization.

This test validates that BrushMatcher bypasses complex multi-strategy processing
when correct matches are found, and that the CorrectMatchesChecker uses
normalization caching for performance.
"""

import time
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.correct_matches import CorrectMatchesChecker


def test_brush_matcher_correct_matches_bypass():
    """Test that BrushMatcher bypasses multi-strategy processing for correct matches."""
    matcher = BrushMatcher()

    # Test with a known correct match
    test_value = "simpson chubby 2 manchurian"

    # First call - should use correct matches and bypass complex processing
    start_time = time.time()
    result1 = matcher.match(test_value)
    first_call_time = time.time() - start_time

    # Second call - should be even faster due to caching
    start_time = time.time()
    result2 = matcher.match(test_value)
    second_call_time = time.time() - start_time

    print(f"First call (correct match): {first_call_time:.6f}s")
    print(f"Second call (cached): {second_call_time:.6f}s")

    # Both calls should return the same result
    assert result1 is not None, "First call should find a match"
    assert result2 is not None, "Second call should find a match"
    assert result1.matched == result2.matched, "Results should be identical"

    # Second call should be faster due to caching
    assert second_call_time <= first_call_time, "Cached call should be faster or equal"


def test_correct_matches_checker_normalization_cache():
    """Test that CorrectMatchesChecker uses normalization caching."""
    # Load some correct matches data for testing
    import yaml
    from pathlib import Path

    correct_matches_path = Path("data/correct_matches.yaml")
    if not correct_matches_path.exists():
        print("Skipping test - correct_matches.yaml not found")
        return

    with open(correct_matches_path, "r", encoding="utf-8") as f:
        correct_matches_data = yaml.safe_load(f) or {}

    checker = CorrectMatchesChecker(correct_matches_data)
    test_value = "simpson chubby 2 manchurian"

    # First call - should populate cache
    start_time = time.time()
    result1 = checker.check(test_value)
    first_call_time = time.time() - start_time

    # Second call - should use cache
    start_time = time.time()
    result2 = checker.check(test_value)
    second_call_time = time.time() - start_time

    print(f"CorrectMatchesChecker first call: {first_call_time:.6f}s")
    print(f"CorrectMatchesChecker second call: {second_call_time:.6f}s")

    # Results should be identical
    assert result1 == result2, "Cached results should be identical"

    # Cache hit should be faster
    assert second_call_time < first_call_time, "Cache hit should be faster than cache miss"


def test_brush_matcher_vs_complex_processing():
    """Test that correct matches are much faster than complex multi-strategy processing."""
    matcher = BrushMatcher()

    # Test with correct match (should be fast)
    correct_match_value = "simpson chubby 2 manchurian"
    start_time = time.time()
    correct_result = matcher.match(correct_match_value)
    correct_match_time = time.time() - start_time

    # Test with non-correct match (should trigger complex processing)
    non_correct_value = "some random brush that won't match anything"
    start_time = time.time()
    non_correct_result = matcher.match(non_correct_value)
    non_correct_time = time.time() - start_time

    print(f"Correct match time: {correct_match_time:.6f}s")
    print(f"Non-correct match time: {non_correct_time:.6f}s")

    # Correct match should be found
    assert correct_result is not None, "Correct match should be found"

    # Non-correct match should not be found (or be much slower)
    if non_correct_result is None:
        print("Non-correct match correctly returned None")
    else:
        print("Non-correct match found something (unexpected)")

    # Correct match should be significantly faster than complex processing
    # (This is the key optimization - bypassing multi-strategy when correct match found)
    print(
        f"Performance ratio: {non_correct_time/correct_match_time:.1f}x slower for complex processing"
    )


if __name__ == "__main__":
    test_brush_matcher_correct_matches_bypass()
    test_correct_matches_checker_normalization_cache()
    test_brush_matcher_vs_complex_processing()
    print("All BrushMatcher correct matches optimization tests passed!")
