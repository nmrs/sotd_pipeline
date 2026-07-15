#!/usr/bin/env python3
"""Tests for soap scent counting rules."""

from sotd.aggregate.utils.soap_scent_filter import counts_as_distinct_soap_scent, is_mashup_soap


class TestSoapScentFilter:
    def test_is_mashup_soap(self):
        assert is_mashup_soap({"enriched": {"is_mashup": True}}) is True
        assert is_mashup_soap({"enriched": {"is_mashup": False}}) is False
        assert is_mashup_soap(None) is False

    def test_counts_as_distinct_excludes_mashup(self):
        soap = {
            "matched": {"brand": "Stirling Soap Co.", "scent": "Sample Mash Up"},
            "enriched": {"is_mashup": True},
        }
        assert counts_as_distinct_soap_scent(soap) is False

    def test_counts_as_distinct_excludes_non_countable(self):
        soap = {
            "matched": {
                "brand": "Mama Bear's Soaps",
                "scent": "Sample Mashup",
                "countable": False,
            },
            "enriched": {},
        }
        assert counts_as_distinct_soap_scent(soap) is False

    def test_counts_as_distinct_includes_normal_scent(self):
        soap = {
            "matched": {"brand": "Barrister and Mann", "scent": "Seville"},
            "enriched": {},
        }
        assert counts_as_distinct_soap_scent(soap) is True
