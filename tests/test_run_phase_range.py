"""Tests for community-phase wiring in the root run.py dispatch."""

import pytest

from run import get_phase_range


def test_community_single_phase():
    assert get_phase_range("community") == ["community"]


def test_default_pipeline_excludes_community():
    assert get_phase_range("") == ["fetch", "extract", "match", "enrich", "aggregate", "report"]


def test_fetch_json_still_excluded_from_default():
    assert "fetch_json" not in get_phase_range("")


def test_ranges_involving_community_are_rejected():
    with pytest.raises(ValueError):
        get_phase_range("fetch:community")
    with pytest.raises(ValueError):
        get_phase_range("community:report")
