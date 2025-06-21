#!/usr/bin/env python3
"""Tests for annual aggregator functionality."""

from sotd.aggregate.aggregators.annual_aggregator import (
    AnnualAggregator,
    aggregate_annual_blades,
    aggregate_annual_brushes,
    aggregate_annual_razors,
    aggregate_annual_soaps,
    create_annual_blade_aggregator,
    create_annual_brush_aggregator,
    create_annual_razor_aggregator,
    create_annual_soap_aggregator,
)


class TestAnnualAggregator:
    """Test AnnualAggregator class."""

    def test_init(self):
        """Test AnnualAggregator initialization."""
        aggregator = AnnualAggregator("razors")
        assert aggregator.category == "razors"

    def test_aggregate_from_monthly_data_empty(self):
        """Test aggregation with empty monthly data."""
        aggregator = AnnualAggregator("razors")
        result = aggregator.aggregate_from_monthly_data({})
        assert result == []

    def test_aggregate_from_monthly_data_single_month(self):
        """Test aggregation with single month data."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Razor B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            }
        }

        aggregator = AnnualAggregator("razors")
        result = aggregator.aggregate_from_monthly_data(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Razor A"
        assert result[0]["shaves"] == 10
        assert result[0]["unique_users"] == 5
        assert result[0]["position"] == 1
        assert result[1]["name"] == "Razor B"
        assert result[1]["shaves"] == 8
        assert result[1]["unique_users"] == 4
        assert result[1]["position"] == 2

    def test_aggregate_from_monthly_data_multiple_months(self):
        """Test aggregation with multiple months data."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Razor B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            },
            "2024-02": {
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 15, "unique_users": 7, "position": 1},
                        {"name": "Razor C", "shaves": 12, "unique_users": 6, "position": 2},
                    ]
                }
            },
        }

        aggregator = AnnualAggregator("razors")
        result = aggregator.aggregate_from_monthly_data(monthly_data)

        assert len(result) == 3
        # Razor A should be first (25 total shaves)
        assert result[0]["name"] == "Razor A"
        assert result[0]["shaves"] == 25
        assert result[0]["unique_users"] == 12
        assert result[0]["position"] == 1
        # Razor C should be second (12 shaves)
        assert result[1]["name"] == "Razor C"
        assert result[1]["shaves"] == 12
        assert result[1]["unique_users"] == 6
        assert result[1]["position"] == 2
        # Razor B should be third (8 shaves)
        assert result[2]["name"] == "Razor B"
        assert result[2]["shaves"] == 8
        assert result[2]["unique_users"] == 4
        assert result[2]["position"] == 3

    def test_aggregate_from_monthly_data_missing_category(self):
        """Test aggregation when category is missing from monthly data."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "blades": [
                        {"name": "Blade A", "shaves": 10, "unique_users": 5, "position": 1},
                    ]
                }
            }
        }

        aggregator = AnnualAggregator("razors")
        result = aggregator.aggregate_from_monthly_data(monthly_data)
        assert result == []

    def test_aggregate_from_monthly_data_invalid_structure(self):
        """Test aggregation with invalid monthly data structure."""
        monthly_data = {"2024-01": {"data": {"razors": "not a list"}}}

        aggregator = AnnualAggregator("razors")
        result = aggregator.aggregate_from_monthly_data(monthly_data)
        assert result == []

    def test_convert_monthly_to_records(self):
        """Test conversion of monthly data to records format."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Razor B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            }
        }

        aggregator = AnnualAggregator("razors")
        records = aggregator._convert_monthly_to_records(monthly_data)

        assert len(records) == 2
        assert records[0]["name"] == "Razor A"
        assert records[0]["shaves"] == 10
        assert records[0]["unique_users"] == 5
        assert records[0]["position"] == 1
        assert records[1]["name"] == "Razor B"
        assert records[1]["shaves"] == 8
        assert records[1]["unique_users"] == 4
        assert records[1]["position"] == 2

    def test_extract_data(self):
        """Test data extraction from records."""
        records = [
            {"name": "Razor A", "shaves": 10, "unique_users": 5, "position": 1},
            {"name": "Razor B", "shaves": 8, "unique_users": 4, "position": 2},
        ]

        aggregator = AnnualAggregator("razors")
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["name"] == "Razor A"
        assert extracted[0]["shaves"] == 10
        assert extracted[0]["unique_users"] == 5
        assert extracted[1]["name"] == "Razor B"
        assert extracted[1]["shaves"] == 8
        assert extracted[1]["unique_users"] == 4

    def test_extract_data_missing_fields(self):
        """Test data extraction with missing fields."""
        records = [
            {"name": "Razor A", "shaves": 10},  # missing unique_users
            {"name": "Razor B", "unique_users": 4},  # missing shaves
            {"shaves": 5, "unique_users": 3},  # missing name
        ]

        aggregator = AnnualAggregator("razors")
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 0

    def test_create_composite_name(self):
        """Test composite name creation."""
        import pandas as pd

        df = pd.DataFrame(
            [
                {"name": "Razor A", "shaves": 10, "unique_users": 5},
                {"name": "Razor B", "shaves": 8, "unique_users": 4},
            ]
        )

        aggregator = AnnualAggregator("razors")
        names = aggregator._create_composite_name(df)

        assert list(names) == ["Razor A", "Razor B"]

    def test_group_and_aggregate(self):
        """Test grouping and aggregation."""
        import pandas as pd

        df = pd.DataFrame(
            [
                {"name": "Razor A", "shaves": 10, "unique_users": 5},
                {"name": "Razor A", "shaves": 15, "unique_users": 7},
                {"name": "Razor B", "shaves": 8, "unique_users": 4},
            ]
        )

        aggregator = AnnualAggregator("razors")
        grouped = aggregator._group_and_aggregate(df)

        assert len(grouped) == 2
        razor_a = grouped[grouped["name"] == "Razor A"].iloc[0]
        razor_b = grouped[grouped["name"] == "Razor B"].iloc[0]

        assert razor_a["shaves"] == 25
        assert razor_a["unique_users"] == 12
        assert razor_b["shaves"] == 8
        assert razor_b["unique_users"] == 4


class TestFactoryFunctions:
    """Test factory functions for creating annual aggregators."""

    def test_create_annual_razor_aggregator(self):
        """Test creating razor aggregator."""
        aggregator = create_annual_razor_aggregator()
        assert isinstance(aggregator, AnnualAggregator)
        assert aggregator.category == "razors"

    def test_create_annual_blade_aggregator(self):
        """Test creating blade aggregator."""
        aggregator = create_annual_blade_aggregator()
        assert isinstance(aggregator, AnnualAggregator)
        assert aggregator.category == "blades"

    def test_create_annual_brush_aggregator(self):
        """Test creating brush aggregator."""
        aggregator = create_annual_brush_aggregator()
        assert isinstance(aggregator, AnnualAggregator)
        assert aggregator.category == "brushes"

    def test_create_annual_soap_aggregator(self):
        """Test creating soap aggregator."""
        aggregator = create_annual_soap_aggregator()
        assert isinstance(aggregator, AnnualAggregator)
        assert aggregator.category == "soaps"


class TestLegacyFunctions:
    """Test legacy function interfaces."""

    def test_aggregate_annual_razors(self):
        """Test aggregate_annual_razors function."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Razor B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            }
        }

        result = aggregate_annual_razors(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Razor A"
        assert result[0]["shaves"] == 10
        assert result[0]["unique_users"] == 5
        assert result[0]["position"] == 1

    def test_aggregate_annual_blades(self):
        """Test aggregate_annual_blades function."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "blades": [
                        {"name": "Blade A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Blade B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            }
        }

        result = aggregate_annual_blades(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Blade A"
        assert result[0]["shaves"] == 10
        assert result[0]["unique_users"] == 5
        assert result[0]["position"] == 1

    def test_aggregate_annual_brushes(self):
        """Test aggregate_annual_brushes function."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "brushes": [
                        {"name": "Brush A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Brush B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            }
        }

        result = aggregate_annual_brushes(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Brush A"
        assert result[0]["shaves"] == 10
        assert result[0]["unique_users"] == 5
        assert result[0]["position"] == 1

    def test_aggregate_annual_soaps(self):
        """Test aggregate_annual_soaps function."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "soaps": [
                        {"name": "Soap A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Soap B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            }
        }

        result = aggregate_annual_soaps(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Soap A"
        assert result[0]["shaves"] == 10
        assert result[0]["unique_users"] == 5
        assert result[0]["position"] == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_monthly_data(self):
        """Test with completely empty monthly data."""
        result = aggregate_annual_razors({})
        assert result == []

    def test_monthly_data_without_data_section(self):
        """Test monthly data without data section."""
        monthly_data = {"2024-01": {"meta": {"total_shaves": 100}}}

        result = aggregate_annual_razors(monthly_data)
        assert result == []

    def test_monthly_data_with_invalid_category_data(self):
        """Test monthly data with invalid category data."""
        monthly_data = {"2024-01": {"data": {"razors": "not a list"}}}

        result = aggregate_annual_razors(monthly_data)
        assert result == []

    def test_monthly_data_with_missing_name_field(self):
        """Test monthly data with items missing name field."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "razors": [
                        {"shaves": 10, "unique_users": 5, "position": 1},  # missing name
                        {"name": "Razor B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            }
        }

        result = aggregate_annual_razors(monthly_data)
        assert len(result) == 1
        assert result[0]["name"] == "Razor B"

    def test_multiple_months_with_overlapping_products(self):
        """Test multiple months with overlapping product names."""
        monthly_data = {
            "2024-01": {
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 10, "unique_users": 5, "position": 1},
                        {"name": "Razor B", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            },
            "2024-02": {
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 15, "unique_users": 7, "position": 1},
                        {"name": "Razor C", "shaves": 12, "unique_users": 6, "position": 2},
                    ]
                }
            },
            "2024-03": {
                "data": {
                    "razors": [
                        {"name": "Razor B", "shaves": 5, "unique_users": 3, "position": 1},
                        {"name": "Razor C", "shaves": 8, "unique_users": 4, "position": 2},
                    ]
                }
            },
        }

        result = aggregate_annual_razors(monthly_data)

        assert len(result) == 3
        # Razor A should be first (25 total shaves)
        assert result[0]["name"] == "Razor A"
        assert result[0]["shaves"] == 25
        assert result[0]["unique_users"] == 12
        assert result[0]["position"] == 1
        # Razor C should be second (20 total shaves)
        assert result[1]["name"] == "Razor C"
        assert result[1]["shaves"] == 20
        assert result[1]["unique_users"] == 10
        assert result[1]["position"] == 2
        # Razor B should be third (13 total shaves)
        assert result[2]["name"] == "Razor B"
        assert result[2]["shaves"] == 13
        assert result[2]["unique_users"] == 7
        assert result[2]["position"] == 3
