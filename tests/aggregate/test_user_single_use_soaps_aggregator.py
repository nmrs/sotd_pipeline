#!/usr/bin/env python3
"""Tests for UserSingleUseSoapsAggregator."""

from sotd.aggregate.aggregators.users.user_single_use_soaps_aggregator import (
    UserSingleUseSoapsAggregator,
    aggregate_user_single_use_soaps,
)


def _soap_record(author: str, brand: str, scent: str, **soap_extra) -> dict:
    matched = {"brand": brand, "scent": scent, "countable": True}
    matched.update(soap_extra.pop("matched", {}))
    soap = {"matched": matched, **soap_extra}
    return {"author": author, "soap": soap}


class TestUserSingleUseSoapsAggregator:
    def test_one_point_when_sole_user_uses_soap_many_times(self):
        records = [
            _soap_record("alice", "Brand A", "Scent 1"),
            _soap_record("alice", "Brand A", "Scent 1"),
            _soap_record("alice", "Brand A", "Scent 1"),
        ]
        result = aggregate_user_single_use_soaps(records)
        assert len(result) == 1
        assert result[0]["user"] == "alice"
        assert result[0]["single_use_soaps"] == 1
        assert result[0]["shaves"] == 3

    def test_no_points_when_two_users_share_soap(self):
        records = [
            _soap_record("alice", "Brand A", "Scent 1"),
            _soap_record("bob", "Brand A", "Scent 1"),
        ]
        result = aggregate_user_single_use_soaps(records)
        assert result == []

    def test_multiple_exclusive_soaps_for_one_user(self):
        records = [
            _soap_record("alice", "Brand A", "Scent 1"),
            _soap_record("alice", "Brand B", "Scent 2"),
            _soap_record("bob", "Brand C", "Scent 3"),
        ]
        result = aggregate_user_single_use_soaps(records)
        assert len(result) == 2
        by_user = {row["user"]: row for row in result}
        assert by_user["alice"]["single_use_soaps"] == 2
        assert by_user["bob"]["single_use_soaps"] == 1

    def test_skips_mashups(self):
        records = [
            {
                "author": "alice",
                "soap": {
                    "matched": {"brand": "Mix", "scent": "Blend", "countable": True},
                    "enriched": {"is_mashup": True},
                },
            },
        ]
        result = aggregate_user_single_use_soaps(records)
        assert result == []

    def test_skips_non_countable_soaps(self):
        records = [
            _soap_record("alice", "Brand A", "Scent 1", matched={"countable": False}),
        ]
        result = aggregate_user_single_use_soaps(records)
        assert result == []

    def test_case_insensitive_soap_grouping(self):
        records = [
            _soap_record("alice", "Brand A", "Scent 1"),
            _soap_record("bob", "brand a", "scent 1"),
        ]
        result = aggregate_user_single_use_soaps(records)
        assert result == []

    def test_ranking_tiebreaker_by_shaves(self):
        records = [
            _soap_record("alice", "Brand A", "Scent 1"),
            _soap_record("alice", "Brand A", "Scent 1"),
            _soap_record("bob", "Brand B", "Scent 2"),
        ]
        result = aggregate_user_single_use_soaps(records)
        assert result[0]["user"] == "alice"
        assert result[0]["rank"] == 1
        assert result[1]["user"] == "bob"
        assert result[1]["rank"] == 2

    def test_extract_skips_missing_brand(self):
        aggregator = UserSingleUseSoapsAggregator()
        records = [{"author": "alice", "soap": {"matched": {"scent": "X"}}}]
        assert aggregator._extract_data(records) == []
