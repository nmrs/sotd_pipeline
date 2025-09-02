#!/usr/bin/env python3
"""Tests for BrushDiversityAggregator."""

from sotd.aggregate.aggregators.users.brush_diversity_aggregator import (
    BrushDiversityAggregator,
    aggregate_brush_diversity,
)


class TestBrushDiversityAggregator:
    """Test BrushDiversityAggregator functionality."""

    def test_extract_data_with_full_brush_info(self):
        """Test data extraction with complete brush information."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot": {
                            "brand": "Declaration",
                            "model": "B2",
                        },
                        "handle": {
                            "brand": "Dogwood",
                        },
                    },
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "knot": {
                            "brand": "Simpson",
                            "model": "Best Badger",
                        },
                        "handle": {
                            "brand": "Simpson",
                        },
                    },
                },
            },
        ]

        aggregator = BrushDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["brand"] == "Declaration"
        assert extracted[0]["model"] == "B2"
        assert extracted[0]["knot_brand"] == "Declaration"
        assert extracted[0]["knot_model"] == "B2"
        assert extracted[0]["handle_brand"] == "Dogwood"
        assert extracted[0]["author"] == "user1"

        assert extracted[1]["brand"] == "Simpson"
        assert extracted[1]["model"] == "Chubby 2"
        assert extracted[1]["knot_brand"] == "Simpson"
        assert extracted[1]["knot_model"] == "Best Badger"
        assert extracted[1]["handle_brand"] == "Simpson"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_with_partial_brush_info(self):
        """Test data extraction with partial brush information."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        # Missing knot and handle info
                    },
                },
            },
        ]

        aggregator = BrushDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Declaration"
        assert extracted[0]["model"] == "B2"
        assert extracted[0]["knot_brand"] is None
        assert extracted[0]["knot_model"] is None
        assert extracted[0]["handle_brand"] is None

    def test_extract_data_skips_records_without_brand(self):
        """Test that records without brand are skipped."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "model": "B2",
                        "knot_brand": "Declaration",
                    },
                },
            },
        ]

        aggregator = BrushDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 0

    def test_extract_data_skips_records_without_model(self):
        """Test that records without model are skipped."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "knot_brand": "Declaration",
                    },
                },
            },
        ]

        aggregator = BrushDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 0

    def test_extract_data_skips_records_without_matched_brush(self):
        """Test that records without matched brush are skipped."""
        records = [
            {
                "author": "user1",
                "brush": {},
            },
        ]

        aggregator = BrushDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 0

    def test_create_composite_name_with_full_info(self):
        """Test composite name creation with complete brush information."""
        aggregator = BrushDiversityAggregator()

        import pandas as pd

        df = pd.DataFrame(
            {
                "brand": ["Declaration", "Simpson"],
                "model": ["B2", "Chubby 2"],
                "knot_brand": ["Declaration", "Simpson"],
                "knot_model": ["B2", "Best Badger"],
                "handle_brand": ["Dogwood", "Simpson"],
            }
        )

        composite_names = aggregator._create_composite_name(df)

        assert composite_names.iloc[0] == ("Declaration B2 knot:Declaration knot:B2 handle:Dogwood")
        assert composite_names.iloc[1] == (
            "Simpson Chubby 2 knot:Simpson knot:Best Badger handle:Simpson"
        )

    def test_create_composite_name_with_partial_info(self):
        """Test composite name creation with partial brush information."""
        aggregator = BrushDiversityAggregator()

        import pandas as pd

        df = pd.DataFrame(
            {
                "brand": ["Declaration", "Simpson"],
                "model": ["B2", "Chubby 2"],
                "knot_brand": ["Declaration", None],
                "knot_model": ["B2", None],
                "handle_brand": [None, "Simpson"],
            }
        )

        composite_names = aggregator._create_composite_name(df)

        assert composite_names.iloc[0] == "Declaration B2 knot:Declaration knot:B2"
        assert composite_names.iloc[1] == "Simpson Chubby 2 handle:Simpson"

    def test_aggregate_brush_diversity(self):
        """Test complete aggregation of brush diversity data."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot_brand": "Declaration",
                        "knot_model": "B2",
                        "handle_brand": "Dogwood",
                    },
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot_brand": "Declaration",
                        "knot_model": "B2",
                        "handle_brand": "Dogwood",
                    },
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "knot_brand": "Simpson",
                        "knot_model": "Best Badger",
                        "handle_brand": "Simpson",
                    },
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot_brand": "Declaration",
                        "knot_model": "B2",
                        "handle_brand": "Dogwood",
                    },
                },
            },
        ]

        result = aggregate_brush_diversity(records)

        assert len(result) == 2

        # Check first result (user1 with 2 unique brushes, 3 total shaves)
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_brushes"] == 2
        assert result[0]["shaves"] == 3
        assert result[0]["avg_shaves_per_brush"] == 1.5

        # Check second result (user2 with 1 unique brush, 1 total shave)
        assert result[1]["rank"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["unique_brushes"] == 1
        assert result[1]["shaves"] == 1
        assert result[1]["avg_shaves_per_brush"] == 1.0

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_brush_diversity([])
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

        result = aggregate_brush_diversity(records)
        assert result == []

    def test_aggregate_single_user_multiple_brushes(self):
        """Test aggregation for single user with multiple brushes."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot_brand": "Declaration",
                        "knot_model": "B2",
                        "handle_brand": "Dogwood",
                    },
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "knot_brand": "Simpson",
                        "knot_model": "Best Badger",
                        "handle_brand": "Simpson",
                    },
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Mühle",
                        "model": "Silvertip",
                        "knot_brand": "Mühle",
                        "knot_model": "Silvertip",
                        "handle_brand": "Mühle",
                    },
                },
            },
        ]

        result = aggregate_brush_diversity(records)

        assert len(result) == 1
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_brushes"] == 3
        assert result[0]["shaves"] == 3
        assert result[0]["avg_shaves_per_brush"] == 1.0

    def test_aggregate_same_brush_multiple_shaves(self):
        """Test aggregation for same brush used multiple times."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot_brand": "Declaration",
                        "knot_model": "B2",
                        "handle_brand": "Dogwood",
                    },
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot_brand": "Declaration",
                        "knot_model": "B2",
                        "handle_brand": "Dogwood",
                    },
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Declaration",
                        "model": "B2",
                        "knot_brand": "Declaration",
                        "knot_model": "B2",
                        "handle_brand": "Dogwood",
                    },
                },
            },
        ]

        result = aggregate_brush_diversity(records)

        assert len(result) == 1
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_brushes"] == 1
        assert result[0]["shaves"] == 3
        assert result[0]["avg_shaves_per_brush"] == 3.0
