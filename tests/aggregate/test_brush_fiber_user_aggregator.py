#!/usr/bin/env python3
"""Tests for BrushFiberUserAggregator."""

from sotd.aggregate.aggregators.users.brush_fiber_user_aggregator import (
    BrushFiberUserAggregator,
    aggregate_brush_fiber_users,
)


class TestBrushFiberUserAggregator:
    """Test BrushFiberUserAggregator functionality."""

    def test_extract_data_with_fiber_info(self):
        """Test data extraction with brush fiber information."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {"fiber": "synthetic"},
                },
            },
        ]

        aggregator = BrushFiberUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["fiber"] == "badger"
        assert extracted[0]["author"] == "user1"
        assert extracted[1]["fiber"] == "synthetic"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_skips_records_without_fiber(self):
        """Test that records without fiber are skipped."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {"brand": "Declaration"},
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {"fiber": "badger", "brand": "Declaration"},
                },
            },
        ]

        aggregator = BrushFiberUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["fiber"] == "badger"
        assert extracted[0]["author"] == "user2"

    def test_extract_data_skips_records_without_author(self):
        """Test that records without author are skipped."""
        records = [
            {
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {"fiber": "synthetic"},
                },
            },
        ]

        aggregator = BrushFiberUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["fiber"] == "synthetic"
        assert extracted[0]["author"] == "user2"

    def test_extract_data_skips_records_without_matched_brush(self):
        """Test that records without matched brush are skipped."""
        records = [
            {
                "author": "user1",
                "brush": {},
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
        ]

        aggregator = BrushFiberUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["fiber"] == "badger"
        assert extracted[0]["author"] == "user2"

    def test_group_and_aggregate_by_fiber_and_user(self):
        """Test grouping by fiber and user."""
        aggregator = BrushFiberUserAggregator()
        
        import pandas as pd
        df = pd.DataFrame({
            "fiber": ["badger", "badger", "synthetic", "synthetic"],
            "author": ["user1", "user2", "user1", "user3"],
        })
        
        grouped = aggregator._group_and_aggregate(df)
        
        assert len(grouped) == 4
        assert grouped.iloc[0]["fiber"] == "badger"
        assert grouped.iloc[0]["author"] == "user1"
        assert grouped.iloc[0]["shaves"] == 1
        assert grouped.iloc[1]["fiber"] == "badger"
        assert grouped.iloc[1]["author"] == "user2"
        assert grouped.iloc[1]["shaves"] == 1

    def test_sort_and_rank_with_multiple_fibers(self):
        """Test sorting and ranking with multiple fiber types."""
        aggregator = BrushFiberUserAggregator()
        
        import pandas as pd
        df = pd.DataFrame({
            "fiber": ["badger", "badger", "boar", "boar", "synthetic"],
            "author": ["user1", "user2", "user1", "user3", "user4"],
            "shaves": [5, 3, 8, 2, 1],
            "unique_users": [1, 1, 1, 1, 1],
        })
        
        result = aggregator._sort_and_rank(df)
        
        assert len(result) == 5
        
        # Check badger fiber (alphabetically first)
        assert result[0]["fiber"] == "badger"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 5
        
        assert result[1]["fiber"] == "badger"
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 3
        
        # Check boar fiber
        assert result[2]["fiber"] == "boar"
        assert result[2]["position"] == 1
        assert result[2]["user"] == "user1"
        assert result[2]["shaves"] == 8
        
        assert result[3]["fiber"] == "boar"
        assert result[3]["position"] == 2
        assert result[3]["user"] == "user3"
        assert result[3]["shaves"] == 2
        
        # Check synthetic fiber
        assert result[4]["fiber"] == "synthetic"
        assert result[4]["position"] == 1
        assert result[4]["user"] == "user4"
        assert result[4]["shaves"] == 1

    def test_aggregate_brush_fiber_users(self):
        """Test complete aggregation of brush fiber usage data."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "synthetic"},
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user3",
                "brush": {
                    "matched": {"fiber": "synthetic"},
                },
            },
        ]

        result = aggregate_brush_fiber_users(records)

        assert len(result) == 4
        
        # Check badger fiber (alphabetically first)
        assert result[0]["fiber"] == "badger"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        
        assert result[1]["fiber"] == "badger"
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1
        
        # Check synthetic fiber
        assert result[2]["fiber"] == "synthetic"
        assert result[2]["position"] == 1
        assert result[2]["user"] == "user1"
        assert result[2]["shaves"] == 1
        assert result[2]["unique_users"] == 1
        
        assert result[3]["fiber"] == "synthetic"
        assert result[3]["position"] == 2
        assert result[3]["user"] == "user3"
        assert result[3]["shaves"] == 1
        assert result[3]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_brush_fiber_users([])
        assert result == []

    def test_aggregate_no_brush_records(self):
        """Test aggregation with no brush records."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {"brand": "Declaration"},
                },
            },
        ]

        result = aggregate_brush_fiber_users(records)
        assert result == []

    def test_aggregate_single_fiber_multiple_users(self):
        """Test aggregation for single fiber with multiple users."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user3",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
        ]

        result = aggregate_brush_fiber_users(records)

        assert len(result) == 3
        assert result[0]["fiber"] == "badger"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 1
        assert result[1]["fiber"] == "badger"
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[2]["fiber"] == "badger"
        assert result[2]["position"] == 3
        assert result[2]["user"] == "user3"
        assert result[2]["shaves"] == 1

    def test_aggregate_same_user_same_fiber_multiple_shaves(self):
        """Test aggregation for same user using same fiber multiple times."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
        ]

        result = aggregate_brush_fiber_users(records)

        assert len(result) == 1
        assert result[0]["fiber"] == "badger"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 3
        assert result[0]["unique_users"] == 1

    def test_aggregate_with_various_fiber_types(self):
        """Test aggregation with various common fiber types."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {"fiber": "badger"},
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {"fiber": "boar"},
                },
            },
            {
                "author": "user3",
                "brush": {
                    "matched": {"fiber": "synthetic"},
                },
            },
            {
                "author": "user4",
                "brush": {
                    "matched": {"fiber": "horse"},
                },
            },
            {
                "author": "user5",
                "brush": {
                    "matched": {"fiber": "mixed"},
                },
            },
        ]

        result = aggregate_brush_fiber_users(records)

        assert len(result) == 5
        
        # Check alphabetical ordering
        assert result[0]["fiber"] == "badger"
        assert result[1]["fiber"] == "boar"
        assert result[2]["fiber"] == "horse"
        assert result[3]["fiber"] == "mixed"
        assert result[4]["fiber"] == "synthetic"
        
        # All should have position 1 since only one user per fiber
        for item in result:
            assert item["position"] == 1
            assert item["shaves"] == 1
            assert item["unique_users"] == 1
