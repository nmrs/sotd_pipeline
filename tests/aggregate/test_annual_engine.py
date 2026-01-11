"""
Tests for the annual aggregation engine.

Tests the functionality for combining monthly aggregated data into annual summaries.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from sotd.aggregate.annual_engine import (
    AnnualAggregationEngine,
    aggregate_monthly_data,
    process_annual,
    process_annual_range,
)


class TestAnnualAggregationEngine:
    """Test the AnnualAggregationEngine class."""

    def test_init_with_valid_year(self):
        """Test initialization with valid year."""
        engine = AnnualAggregationEngine("2024", Path("/data"))
        assert engine.year == "2024"
        assert engine.data_dir == Path("/data")

    def test_init_with_invalid_year_format(self):
        """Test initialization with invalid year format."""
        with pytest.raises(ValueError, match="Year must be in YYYY format"):
            AnnualAggregationEngine("24", Path("/data"))

    def test_init_with_non_numeric_year(self):
        """Test initialization with non-numeric year."""
        with pytest.raises(ValueError, match="Year must be numeric"):
            AnnualAggregationEngine("abcd", Path("/data"))

    def test_aggregate_razors_single_month(self):
        """Test aggregating razors from a single month."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 30, "unique_users": 25},
                        {"name": "Razor B", "shaves": 20, "unique_users": 15},
                    ],
                },
            }
        }

        result = engine.aggregate_razors(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Razor A"
        assert result[0]["shaves"] == 30
        assert result[0]["unique_users"] == 25
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "Razor B"
        assert result[1]["shaves"] == 20
        assert result[1]["unique_users"] == 15
        assert result[1]["rank"] == 2

    def test_aggregate_razors_multiple_months(self):
        """Test aggregating razors from multiple months."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 30, "unique_users": 25},
                        {"name": "Razor B", "shaves": 20, "unique_users": 15},
                    ],
                },
            },
            "2024-02": {
                "meta": {"total_shaves": 80, "unique_shavers": 40},
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 25, "unique_users": 20},
                        {"name": "Razor C", "shaves": 15, "unique_users": 10},
                    ],
                },
            },
        }

        result = engine.aggregate_razors(monthly_data)

        assert len(result) == 3
        # Razor A should be first (30+25=55 shaves)
        assert result[0]["name"] == "Razor A"
        assert result[0]["shaves"] == 55
        assert result[0]["unique_users"] == 45  # 25+20 unique users
        assert result[0]["rank"] == 1
        # Razor B should be second (20 shaves)
        assert result[1]["name"] == "Razor B"
        assert result[1]["shaves"] == 20
        assert result[1]["unique_users"] == 15
        assert result[1]["rank"] == 2
        # Razor C should be third (15 shaves)
        assert result[2]["name"] == "Razor C"
        assert result[2]["shaves"] == 15
        assert result[2]["unique_users"] == 10
        assert result[2]["rank"] == 3

    def test_aggregate_razors_empty_data(self):
        """Test aggregating razors with empty data."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {}
        result = engine.aggregate_razors(monthly_data)
        assert result == []

    def test_aggregate_razors_no_razor_data(self):
        """Test aggregating razors when no razor data exists."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {"meta": {"total_shaves": 100, "unique_shavers": 50}, "data": {"razors": []}}
        }

        result = engine.aggregate_razors(monthly_data)
        assert result == []

    def test_aggregate_blades_single_month(self):
        """Test aggregating blades from a single month."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "blades": [
                        {"name": "Blade A", "shaves": 40, "unique_users": 30},
                        {"name": "Blade B", "shaves": 30, "unique_users": 20},
                    ],
                },
            }
        }

        result = engine.aggregate_blades(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Blade A"
        assert result[0]["shaves"] == 40
        assert result[0]["unique_users"] == 30
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "Blade B"
        assert result[1]["shaves"] == 30
        assert result[1]["unique_users"] == 20
        assert result[1]["rank"] == 2

    def test_aggregate_brushes_single_month(self):
        """Test aggregating brushes from a single month."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "brushes": [
                        {"name": "Brush A", "shaves": 35, "unique_users": 25},
                        {"name": "Brush B", "shaves": 25, "unique_users": 15},
                    ],
                },
            }
        }

        result = engine.aggregate_brushes(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Brush A"
        assert result[0]["shaves"] == 35
        assert result[0]["unique_users"] == 25
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "Brush B"
        assert result[1]["shaves"] == 25
        assert result[1]["unique_users"] == 15
        assert result[1]["rank"] == 2

    def test_aggregate_soaps_single_month(self):
        """Test aggregating soaps from a single month."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "soaps": [
                        {"name": "Soap A", "shaves": 45, "unique_users": 35},
                        {"name": "Soap B", "shaves": 35, "unique_users": 25},
                    ],
                },
            }
        }

        result = engine.aggregate_soaps(monthly_data)

        assert len(result) == 2
        assert result[0]["name"] == "Soap A"
        assert result[0]["shaves"] == 45
        assert result[0]["unique_users"] == 35
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "Soap B"
        assert result[1]["shaves"] == 35
        assert result[1]["unique_users"] == 25
        assert result[1]["rank"] == 2

    def test_generate_metadata_single_month(self):
        """Test generating metadata from a single month."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "razors": [{"name": "Razor A", "shaves": 30, "unique_users": 25}],
                },
            }
        }

        result = engine.generate_metadata(monthly_data)

        assert result["year"] == "2024"
        assert result["total_shaves"] == 100
        assert result["unique_shavers"] == 50
        assert result["included_months"] == ["2024-01"]
        # All other months should be missing
        expected_missing = [f"2024-{month:02d}" for month in range(2, 13)]
        assert result["missing_months"] == expected_missing

    def test_generate_metadata_multiple_months(self):
        """Test generating metadata from multiple months."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "razors": [{"name": "Razor A", "shaves": 30, "unique_users": 25}],
                },
            },
            "2024-02": {
                "meta": {"total_shaves": 80, "unique_shavers": 40},
                "data": {
                    "razors": [{"name": "Razor B", "shaves": 25, "unique_users": 20}],
                },
            },
        }

        result = engine.generate_metadata(monthly_data)

        assert result["year"] == "2024"
        assert result["total_shaves"] == 180  # 100 + 80
        assert result["unique_shavers"] == 90  # 50 + 40
        assert result["included_months"] == ["2024-01", "2024-02"]
        # All other months should be missing
        expected_missing = [f"2024-{month:02d}" for month in range(3, 13)]
        assert result["missing_months"] == expected_missing

    def test_generate_metadata_with_missing_months(self):
        """Test generating metadata with missing months."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "razors": [{"name": "Razor A", "shaves": 30, "unique_users": 25}],
                },
            },
            "2024-03": {
                "meta": {"total_shaves": 80, "unique_shavers": 40},
                "data": {
                    "razors": [{"name": "Razor B", "shaves": 25, "unique_users": 20}],
                },
            },
        }

        result = engine.generate_metadata(monthly_data)

        assert result["year"] == "2024"
        assert result["total_shaves"] == 180  # 100 + 80
        assert result["unique_shavers"] == 90  # 50 + 40
        assert result["included_months"] == ["2024-01", "2024-03"]
        # All months except 2024-01 and 2024-03 should be missing
        expected_missing = ["2024-02"] + [f"2024-{month:02d}" for month in range(4, 13)]
        assert result["missing_months"] == expected_missing

    def test_aggregate_all_categories(self):
        """Test aggregating all categories."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "razors": [{"name": "Razor A", "shaves": 30, "unique_users": 25}],
                    "blades": [{"name": "Blade A", "shaves": 40, "unique_users": 30}],
                    "brushes": [{"name": "Brush A", "shaves": 35, "unique_users": 25}],
                    "soaps": [{"name": "Soap A", "shaves": 45, "unique_users": 35}],
                },
            }
        }

        result = engine.aggregate_all_categories(monthly_data)

        assert "metadata" in result
        assert "razors" in result
        assert "blades" in result
        assert "brushes" in result
        assert "soaps" in result

        assert result["metadata"]["year"] == "2024"
        assert result["metadata"]["total_shaves"] == 100
        assert result["metadata"]["unique_shavers"] == 50

        assert len(result["razors"]) == 1
        assert result["razors"][0]["name"] == "Razor A"
        assert len(result["blades"]) == 1
        assert result["blades"][0]["name"] == "Blade A"
        assert len(result["brushes"]) == 1
        assert result["brushes"][0]["name"] == "Brush A"
        assert len(result["soaps"]) == 1
        assert result["soaps"][0]["name"] == "Soap A"

    def test_aggregate_all_categories_empty_data(self):
        """Test aggregating all categories with empty data."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {}
        result = engine.aggregate_all_categories(monthly_data)

        assert "metadata" in result
        assert result["metadata"]["year"] == "2024"
        assert result["metadata"]["total_shaves"] == 0
        assert result["metadata"]["unique_shavers"] == 0
        assert result["metadata"]["included_months"] == []
        # All 12 months should be missing when no data
        expected_missing = [f"2024-{month:02d}" for month in range(1, 13)]
        assert result["metadata"]["missing_months"] == expected_missing

    def test_aggregate_user_diversity_with_hhi(self):
        """Test annual aggregation of user diversity includes HHI and effective_soaps fields."""
        engine = AnnualAggregationEngine("2024", Path("/data"))

        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "user_soap_brand_scent_diversity": [
                        {
                            "user": "user1",
                            "unique_combinations": 3,
                            "shaves": 10,
                            "avg_shaves_per_combination": 3.33,
                            "hhi": 0.5,
                            "effective_soaps": 2.0,
                        },
                        {
                            "user": "user2",
                            "unique_combinations": 2,
                            "shaves": 5,
                            "avg_shaves_per_combination": 2.5,
                            "hhi": 0.6,
                            "effective_soaps": 1.67,
                        },
                    ],
                },
            },
            "2024-02": {
                "meta": {"total_shaves": 80, "unique_shavers": 40},
                "data": {
                    "user_soap_brand_scent_diversity": [
                        {
                            "user": "user1",
                            "unique_combinations": 2,
                            "shaves": 8,
                            "avg_shaves_per_combination": 4.0,
                            "hhi": 0.4,
                            "effective_soaps": 2.5,
                        },
                        {
                            "user": "user2",
                            "unique_combinations": 1,
                            "shaves": 6,
                            "avg_shaves_per_combination": 6.0,
                            "hhi": 1.0,
                            "effective_soaps": 1.0,
                        },
                    ],
                },
            },
        }

        result = engine._aggregate_user_diversity(monthly_data, "user_soap_brand_scent_diversity")

        assert len(result) == 2
        # user1 should be first (3+2=5 unique combinations, 10+8=18 shaves)
        assert result[0]["user"] == "user1"
        assert result[0]["unique_combinations"] == 5
        assert result[0]["shaves"] == 18
        assert result[0]["avg_shaves_per_combination"] == 3.6
        # HHI and effective_soaps are set to 0.0 as placeholders
        # (cannot be accurately recalculated from monthly summaries alone)
        assert result[0]["hhi"] == 0.0
        assert result[0]["effective_soaps"] == 0.0

        # user2 should be second (2+1=3 unique combinations, 5+6=11 shaves)
        assert result[1]["user"] == "user2"
        assert result[1]["unique_combinations"] == 3
        assert result[1]["shaves"] == 11
        # Rounding: 11 / 3 = 3.666... rounds to 3.7 with round(1)
        assert abs(result[1]["avg_shaves_per_combination"] - 3.7) < 0.01
        assert result[1]["hhi"] == 0.0
        assert result[1]["effective_soaps"] == 0.0


class TestAggregateMonthlyData:
    """Test the aggregate_monthly_data function."""

    def test_aggregate_monthly_data_success(self):
        """Test successful aggregation of monthly data."""
        monthly_data = {
            "2024-01": {
                "meta": {"total_shaves": 100, "unique_shavers": 50},
                "data": {
                    "razors": [{"name": "Razor A", "shaves": 30, "unique_users": 25}],
                },
            },
            "2024-02": {
                "meta": {"total_shaves": 80, "unique_shavers": 40},
                "data": {
                    "razors": [{"name": "Razor A", "shaves": 25, "unique_users": 20}],
                },
            },
        }

        result = aggregate_monthly_data("2024", monthly_data)

        assert "metadata" in result
        assert "razors" in result
        assert result["metadata"]["year"] == "2024"
        assert result["metadata"]["total_shaves"] == 180
        assert result["metadata"]["unique_shavers"] == 90
        assert result["metadata"]["included_months"] == ["2024-01", "2024-02"]
        # All other months should be missing
        expected_missing = [f"2024-{month:02d}" for month in range(3, 13)]
        assert result["metadata"]["missing_months"] == expected_missing

    def test_aggregate_monthly_data_empty(self):
        """Test aggregation with empty monthly data."""
        result = aggregate_monthly_data("2024", {})

        assert "metadata" in result
        assert result["metadata"]["year"] == "2024"
        assert result["metadata"]["total_shaves"] == 0
        assert result["metadata"]["unique_shavers"] == 0
        assert result["metadata"]["included_months"] == []
        # All 12 months should be missing when no data
        expected_missing = [f"2024-{month:02d}" for month in range(1, 13)]
        assert result["metadata"]["missing_months"] == expected_missing


class TestProcessAnnual:
    """Test the process_annual function."""

    @patch("sotd.aggregate.annual_engine.load_annual_data")
    @patch("sotd.aggregate.annual_engine.aggregate_monthly_data")
    @patch("sotd.aggregate.annual_engine.save_annual_data")
    def test_process_annual_success(self, mock_save, mock_aggregate, mock_load):
        """Test successful annual processing."""
        # Mock the load function
        mock_load.return_value = {
            "year": "2024",
            "monthly_data": {
                "2024-01": {
                    "meta": {"total_shaves": 100, "unique_shavers": 50},
                    "data": {"razors": []},
                },
                "2024-02": {
                    "meta": {"total_shaves": 80, "unique_shavers": 40},
                    "data": {"razors": []},
                },
            },
            "included_months": ["2024-01", "2024-02"],
            "missing_months": [],
            "validation_errors": [],
        }

        # Mock the aggregate function
        mock_aggregate.return_value = {
            "metadata": {"year": "2024", "total_shaves": 180, "unique_shavers": 90},
            "razors": [],
        }

        # Mock the save function
        mock_save.return_value = None

        process_annual("2024", Path("/data"), debug=True, force=True)

        # Verify calls
        mock_load.assert_called_once_with("2024", Path("/data/aggregated"))
        mock_aggregate.assert_called_once_with(
            "2024",
            mock_load.return_value["monthly_data"],
            mock_load.return_value["included_months"],
            mock_load.return_value["missing_months"],
        )
        mock_save.assert_called_once_with(mock_aggregate.return_value, "2024", Path("/data"))

    @patch("sotd.aggregate.annual_engine.load_annual_data")
    def test_process_annual_load_error(self, mock_load):
        """Test annual processing with load error."""
        mock_load.side_effect = FileNotFoundError("No data found")

        with pytest.raises(FileNotFoundError):
            process_annual("2024", Path("/data"), debug=True, force=True)

    @patch("sotd.aggregate.annual_engine.load_annual_data")
    @patch("sotd.aggregate.annual_engine.aggregate_monthly_data")
    def test_process_annual_aggregate_error(self, mock_aggregate, mock_load):
        """Test annual processing with aggregation error."""
        mock_load.return_value = {
            "year": "2024",
            "monthly_data": {"2024-01": {"meta": {"total_shaves": 100}, "data": {"razors": []}}},
            "included_months": ["2024-01"],
            "missing_months": [],
            "validation_errors": [],
        }
        mock_aggregate.side_effect = ValueError("Aggregation failed")

        with pytest.raises(ValueError):
            process_annual("2024", Path("/data"), debug=True, force=True)


class TestProcessAnnualRange:
    """Test the process_annual_range function."""

    @patch("sotd.aggregate.annual_engine.process_annual")
    def test_process_annual_range_success(self, mock_process):
        """Test successful annual range processing."""
        years = ["2023", "2024"]
        data_dir = Path("/data")

        process_annual_range(years, data_dir, debug=True, force=True)

        # Verify process_annual called for each year
        assert mock_process.call_count == 2
        mock_process.assert_any_call("2023", data_dir, debug=True, force=True)
        mock_process.assert_any_call("2024", data_dir, debug=True, force=True)

    @patch("sotd.aggregate.annual_engine.process_annual")
    def test_process_annual_range_with_errors(self, mock_process):
        """Test annual range processing with some errors."""
        years = ["2023", "2024", "2025"]
        data_dir = Path("/data")

        # Mock process_annual to fail for 2024
        def mock_process_side_effect(year, data_dir, debug, force):
            if year == "2024":
                raise FileNotFoundError(f"No data for {year}")

        mock_process.side_effect = mock_process_side_effect

        # Should not raise exception, should continue processing other years
        process_annual_range(years, data_dir, debug=True, force=True)

        # Verify process_annual called for all years
        assert mock_process.call_count == 3
        mock_process.assert_any_call("2023", data_dir, debug=True, force=True)
        mock_process.assert_any_call("2024", data_dir, debug=True, force=True)
        mock_process.assert_any_call("2025", data_dir, debug=True, force=True)

    def test_process_annual_range_empty_years(self):
        """Test annual range processing with empty years list."""
        data_dir = Path("/data")

        # Should not raise exception
        process_annual_range([], data_dir, debug=True, force=True)
