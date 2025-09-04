"""Pytest configuration for extract tests to ensure test isolation."""

import pytest


@pytest.fixture(autouse=True)
def clear_extract_caches():
    """Automatically clear extract-related caches before each test to ensure test isolation."""
    from sotd.utils.competition_tags import clear_competition_tags_cache
    from sotd.extract.filter import reset_filter

    # Clear caches before each test
    clear_competition_tags_cache()
    reset_filter()

    yield

    # Clear caches after each test as well (defensive programming)
    clear_competition_tags_cache()
    reset_filter()
