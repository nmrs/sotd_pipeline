"""
Test normalization cache performance optimization for BladeMatcher.
"""

import time
from sotd.match.blade_matcher import BladeMatcher


def test_blade_matcher_normalization_cache():
    """Test that BladeMatcher normalization cache improves performance."""
    matcher = BladeMatcher()
    test_value = "Feather"

    # First call - should populate cache
    start_time = time.time()
    result1 = matcher._collect_all_correct_matches(test_value)
    first_call_time = time.time() - start_time

    # Second call - should use cache
    start_time = time.time()
    result2 = matcher._collect_all_correct_matches(test_value)
    second_call_time = time.time() - start_time

    # Third call - should use cache
    start_time = time.time()
    result3 = matcher._collect_all_correct_matches(test_value)
    third_call_time = time.time() - start_time

    print(f"First call (cache miss): {first_call_time:.6f}s")
    print(f"Second call (cache hit): {second_call_time:.6f}s")
    print(f"Third call (cache hit): {third_call_time:.6f}s")

    # Cache hit should be significantly faster
    assert second_call_time < first_call_time, "Cache hit should be faster than cache miss"
    assert third_call_time < first_call_time, "Cache hit should be faster than cache miss"

    # Results should be identical
    assert result1 == result2 == result3, "Cached results should be identical"


def test_blade_matcher_mixed_values_performance():
    """Test BladeMatcher performance with mixed values (some cached, some not)."""
    matcher = BladeMatcher()

    # Test with repeated values (should benefit from cache)
    repeated_values = ["Feather", "Feather", "Feather", "Feather", "Feather"]

    start_time = time.time()
    for value in repeated_values:
        matcher._collect_all_correct_matches(value)
    repeated_time = time.time() - start_time

    # Test with unique values (no cache benefit)
    matcher.clear_cache()  # Clear cache
    unique_values = ["Feather", "Gillette Silver Blue", "Personna Hair Shaper", "Astra", "Derby"]

    start_time = time.time()
    for value in unique_values:
        matcher._collect_all_correct_matches(value)
    unique_time = time.time() - start_time

    avg_repeated = repeated_time / len(repeated_values)
    avg_unique = unique_time / len(unique_values)

    print(f"Average time with repeated values (cache benefit): {avg_repeated:.6f}s")
    print(f"Average time with unique values (no cache benefit): {avg_unique:.6f}s")

    # Repeated values should be faster due to cache
    assert avg_repeated < avg_unique, "Cached lookups should be faster than uncached"


def test_normalization_cache_size():
    """Test that normalization cache grows appropriately."""
    matcher = BladeMatcher()

    # Initially empty
    assert len(matcher._normalization_cache) == 0

    # Add some values
    test_values = ["Feather", "Gillette Silver Blue", "Personna Hair Shaper"]
    for value in test_values:
        matcher._collect_all_correct_matches(value)

    # Cache should have entries
    assert len(matcher._normalization_cache) == len(test_values)

    # Verify cache contents
    for value in test_values:
        assert value in matcher._normalization_cache
        assert matcher._normalization_cache[value] is not None


if __name__ == "__main__":
    test_blade_matcher_normalization_cache()
    test_blade_matcher_mixed_values_performance()
    test_normalization_cache_size()
    print("All normalization cache tests passed!")
