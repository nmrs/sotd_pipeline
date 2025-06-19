"""Integration tests for the aggregate phase using realistic data."""

import json
import tempfile
from pathlib import Path

import pytest

from sotd.aggregate.engine import (
    aggregate_blade_manufacturers,
    aggregate_blades,
    aggregate_brush_handle_makers,
    aggregate_brush_knot_makers,
    aggregate_brush_fibers,
    aggregate_brush_knot_sizes,
    aggregate_brushes,
    aggregate_razor_manufacturers,
    aggregate_razors,
    aggregate_soap_makers,
    aggregate_soaps,
    aggregate_users,
    calculate_basic_metrics,
    filter_matched_records,
)
from sotd.aggregate.load import load_enriched_data
from sotd.aggregate.save import save_aggregated_data


class TestAggregateIntegration:
    """Integration tests for the aggregate phase."""

    @pytest.fixture
    def sample_enriched_data(self):
        """Sample enriched data for testing."""
        return {
            "meta": {
                "month": "2025-01",
                "extracted_at": "2025-01-21T18:40:00Z",
                "total_comments": 10,
                "matched_comments": 8,
            },
            "data": [
                {
                    "id": "test1",
                    "author": "user1",
                    "created_utc": 1640995200,
                    "body": (
                        "Razor: Karve Christopher Bradley\nBlade: Feather\n"
                        "Brush: Simpson Chubby 2\nSoap: Declaration Grooming"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Karve",
                            "model": "Christopher Bradley",
                            "format": "DE",
                            "match_type": "exact",
                        }
                    },
                    "blade": {
                        "matched": {
                            "brand": "Feather",
                            "model": "Hi-Stainless",
                            "match_type": "exact",
                        }
                    },
                    "brush": {
                        "matched": {
                            "brand": "Simpson",
                            "model": "Chubby 2",
                            "handle_maker": "Simpson",
                            "fiber": "Badger",
                            "knot_size_mm": 27,
                            "match_type": "exact",
                        }
                    },
                    "soap": {
                        "matched": {
                            "maker": "Declaration Grooming",
                            "scent": "Sellout",
                            "match_type": "exact",
                        }
                    },
                },
                {
                    "id": "test2",
                    "author": "user2",
                    "created_utc": 1640995201,
                    "body": (
                        "Razor: Merkur 34C\nBlade: Astra SP\n"
                        "Brush: Elite handle w/ Declaration knot\nSoap: Barrister and Mann"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Merkur",
                            "model": "34C",
                            "format": "DE",
                            "match_type": "exact",
                        }
                    },
                    "blade": {
                        "matched": {
                            "brand": "Astra",
                            "model": "Superior Platinum",
                            "match_type": "exact",
                        }
                    },
                    "brush": {
                        "matched": {
                            "brand": "Declaration Grooming",
                            "model": "B15",
                            "handle_maker": "Elite",
                            "fiber": "Badger",
                            "knot_size_mm": 26,
                            "match_type": "exact",
                        }
                    },
                    "soap": {
                        "matched": {
                            "maker": "Barrister and Mann",
                            "scent": "Seville",
                            "match_type": "exact",
                        }
                    },
                },
                {
                    "id": "test3",
                    "author": "user1",  # Same user as test1
                    "created_utc": 1640995202,
                    "body": (
                        "Razor: Karve Christopher Bradley\nBlade: Feather\n"
                        "Brush: Stirling\nSoap: Declaration Grooming"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Karve",
                            "model": "Christopher Bradley",
                            "format": "DE",
                            "match_type": "exact",
                        }
                    },
                    "blade": {
                        "matched": {
                            "brand": "Feather",
                            "model": "Hi-Stainless",
                            "match_type": "exact",
                        }
                    },
                    "brush": {
                        "matched": {
                            "brand": "Stirling",
                            "model": "Badger",
                            "handle_maker": "Stirling",
                            "fiber": "Badger",
                            "knot_size_mm": 24,
                            "match_type": "exact",
                        }
                    },
                    "soap": {
                        "matched": {
                            "maker": "Declaration Grooming",
                            "scent": "Sellout",
                            "match_type": "exact",
                        }
                    },
                },
                {
                    "id": "test4",
                    "author": "user3",
                    "created_utc": 1640995203,
                    "body": "Razor: Gillette Tech\nBlade: Personna\nBrush: Omega\nSoap: Stirling",
                    "razor": {
                        "matched": {
                            "brand": "Gillette",
                            "model": "Tech",
                            "format": "DE",
                            "match_type": "exact",
                        }
                    },
                    "blade": {
                        "matched": {
                            "brand": "Personna",
                            "model": "Comfort Coated",
                            "match_type": "exact",
                        }
                    },
                    "brush": {
                        "matched": {
                            "brand": "Omega",
                            "model": "10049",
                            "handle_maker": "Omega",
                            "fiber": "Boar",
                            "knot_size_mm": 24,
                            "match_type": "exact",
                        }
                    },
                    "soap": {
                        "matched": {
                            "maker": "Stirling",
                            "scent": "Executive Man",
                            "match_type": "exact",
                        }
                    },
                },
                {
                    "id": "test5",
                    "author": "user4",
                    "created_utc": 1640995204,
                    "body": (
                        "Razor: Blackland Blackbird\nBlade: Feather\nBrush: Zenith\n"
                        "Soap: Declaration Grooming"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Blackland",
                            "model": "Blackbird",
                            "format": "DE",
                            "match_type": "exact",
                        }
                    },
                    "blade": {
                        "matched": {
                            "brand": "Feather",
                            "model": "Hi-Stainless",
                            "match_type": "exact",
                        }
                    },
                    "brush": {
                        "matched": {
                            "brand": "Zenith",
                            "model": "B27",
                            "handle_maker": "Zenith",
                            "fiber": "Boar",
                            "knot_size_mm": 28,
                            "match_type": "exact",
                        }
                    },
                    "soap": {
                        "matched": {
                            "maker": "Declaration Grooming",
                            "scent": "Darkfall",
                            "match_type": "exact",
                        }
                    },
                },
            ],
        }

    def test_end_to_end_aggregation(self, sample_enriched_data):
        """Test complete end-to-end aggregation workflow."""
        # Test data loading simulation
        records = sample_enriched_data["data"]

        # Test filtering matched records
        matched_records = filter_matched_records(records, debug=True)
        assert len(matched_records) == 5  # All records should be matched

        # Test basic metrics calculation
        basic_metrics = calculate_basic_metrics(matched_records, debug=True)
        assert basic_metrics["total_shaves"] == 5
        assert basic_metrics["unique_shavers"] == 4
        assert basic_metrics["avg_shaves_per_user"] == 1.25

        # Test razor aggregation
        razor_results = aggregate_razors(matched_records, debug=True)
        assert len(razor_results) == 4  # 4 unique razors

        # Check Karve Christopher Bradley (used twice by user1)
        karve_result = next(r for r in razor_results if "Karve Christopher Bradley" in r["name"])
        assert karve_result["shaves"] == 2
        assert karve_result["unique_users"] == 1
        assert karve_result["avg_shaves_per_user"] == 2.0

        # Test blade aggregation
        blade_results = aggregate_blades(matched_records, debug=True)
        assert len(blade_results) == 3  # 3 unique blade brands (Feather, Astra, Personna)

        # Check Feather (used 3 times by 2 users)
        feather_result = next(r for r in blade_results if "Feather" in r["name"])
        assert feather_result["shaves"] == 3
        assert feather_result["unique_users"] == 2
        assert feather_result["avg_shaves_per_user"] == 1.5

        # Test soap aggregation
        soap_results = aggregate_soaps(matched_records, debug=True)
        assert len(soap_results) == 4  # 4 unique soaps

        # Check Declaration Grooming Sellout (used 2 times by user1)
        dg_result = next(r for r in soap_results if "Declaration Grooming Sellout" in r["name"])
        assert dg_result["shaves"] == 2
        assert dg_result["unique_users"] == 1
        assert dg_result["avg_shaves_per_user"] == 2.0

        # Test brush aggregation
        brush_results = aggregate_brushes(matched_records, debug=True)
        assert len(brush_results) == 5  # 5 unique brushes

        # Test user aggregation
        user_results = aggregate_users(matched_records, debug=True)
        assert len(user_results) == 4  # 4 unique users

        # Check user1 (2 shaves)
        user1_result = next(r for r in user_results if r["user"] == "user1")
        assert user1_result["shaves"] == 2
        assert user1_result["avg_shaves_per_user"] == 1.0

    def test_file_io_integration(self, sample_enriched_data):
        """Test file I/O integration with realistic data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create enriched data file
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"

            with enriched_file.open("w") as f:
                json.dump(sample_enriched_data, f, indent=2)

            # Load enriched data
            metadata, records = load_enriched_data(enriched_file)
            assert metadata["month"] == "2025-01"
            assert len(records) == 5

            # Process data
            matched_records = filter_matched_records(records)
            basic_metrics = calculate_basic_metrics(matched_records)
            razor_results = aggregate_razors(matched_records)
            blade_results = aggregate_blades(matched_records)
            soap_results = aggregate_soaps(matched_records)
            brush_results = aggregate_brushes(matched_records)
            user_results = aggregate_users(matched_records)
            # Add manufacturer-level aggregations
            razor_manufacturers = aggregate_razor_manufacturers(matched_records)
            blade_manufacturers = aggregate_blade_manufacturers(matched_records)
            soap_makers = aggregate_soap_makers(matched_records)
            brush_knot_makers = aggregate_brush_knot_makers(matched_records)
            brush_handle_makers = aggregate_brush_handle_makers(matched_records)
            brush_fibers = aggregate_brush_fibers(matched_records)
            brush_knot_sizes = aggregate_brush_knot_sizes(matched_records)

            # Create aggregated results
            aggregated_results = {
                "year": 2025,
                "month": 1,
                "status": "success",
                "basic_metrics": basic_metrics,
                "aggregations": {
                    "razors": razor_results,
                    "razor_manufacturers": razor_manufacturers,
                    "blades": blade_results,
                    "blade_manufacturers": blade_manufacturers,
                    "soaps": soap_results,
                    "soap_makers": soap_makers,
                    "brushes": brush_results,
                    "brush_knot_makers": brush_knot_makers,
                    "brush_handle_makers": brush_handle_makers,
                    "brush_fibers": brush_fibers,
                    "brush_knot_sizes": brush_knot_sizes,
                    "users": user_results,
                },
                "summary": {
                    "total_records": len(records),
                    "matched_records": len(matched_records),
                    "razor_count": len(razor_results),
                    "razor_manufacturer_count": len(razor_manufacturers),
                    "blade_count": len(blade_results),
                    "blade_manufacturer_count": len(blade_manufacturers),
                    "soap_count": len(soap_results),
                    "soap_maker_count": len(soap_makers),
                    "brush_count": len(brush_results),
                    "brush_knot_maker_count": len(brush_knot_makers),
                    "brush_handle_maker_count": len(brush_handle_makers),
                    "brush_fiber_count": len(brush_fibers),
                    "brush_knot_size_count": len(brush_knot_sizes),
                    "user_count": len(user_results),
                },
            }

            # Save aggregated data
            aggregated_dir = Path(temp_dir) / "aggregated"
            aggregated_file = aggregated_dir / "2025-01.json"
            save_aggregated_data(aggregated_results, aggregated_file, force=False, debug=True)

            # Verify file was created and has correct structure
            assert aggregated_file.exists()

            with aggregated_file.open("r") as f:
                saved_data = json.load(f)

            assert "meta" in saved_data
            assert "data" in saved_data
            assert saved_data["meta"]["month"] == "2025-01"
            assert saved_data["meta"]["total_shaves"] == 5
            assert saved_data["meta"]["unique_shavers"] == 4
            assert len(saved_data["data"]["razors"]) == 4
            assert len(saved_data["data"]["blades"]) == 3
            assert len(saved_data["data"]["soaps"]) == 4
            assert len(saved_data["data"]["brushes"]) == 5
            assert len(saved_data["data"]["users"]) == 4

    def test_edge_cases_with_realistic_data(self):
        """Test edge cases with realistic data scenarios."""
        # Test with records that have missing or invalid product data
        edge_case_records = [
            {
                "id": "edge1",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Razor: Karve Christopher Bradley",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    }
                },
                # Missing blade, soap, brush
            },
            {
                "id": "edge2",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Blade: Feather",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "match_type": "exact",
                    }
                },
                # Missing razor, soap, brush
            },
            {
                "id": "edge3",
                "author": "user3",
                "created_utc": 1640995202,
                "body": "Soap: Declaration Grooming",
                "soap": {
                    "matched": {
                        "maker": "Declaration Grooming",
                        "scent": "Sellout",
                        "match_type": "exact",
                    }
                },
                # Missing razor, blade, brush
            },
            {
                "id": "edge4",
                "author": "user4",
                "created_utc": 1640995203,
                "body": "Brush: Simpson Chubby 2",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "match_type": "exact",
                    }
                },
                # Missing razor, blade, soap
            },
            {
                "id": "edge5",
                "author": "user5",
                "created_utc": 1640995204,
                "body": "No products mentioned",
                # No product data at all
            },
        ]

        # Test filtering
        matched_records = filter_matched_records(edge_case_records, debug=True)
        assert len(matched_records) == 4  # edge5 should be filtered out

        # Test basic metrics
        basic_metrics = calculate_basic_metrics(matched_records, debug=True)
        assert basic_metrics["total_shaves"] == 4
        assert basic_metrics["unique_shavers"] == 4

        # Test individual aggregations
        razor_results = aggregate_razors(edge_case_records, debug=True)
        assert len(razor_results) == 1  # Only one razor

        blade_results = aggregate_blades(edge_case_records, debug=True)
        assert len(blade_results) == 1  # Only one blade

        soap_results = aggregate_soaps(edge_case_records, debug=True)
        assert len(soap_results) == 1  # Only one soap

        brush_results = aggregate_brushes(edge_case_records, debug=True)
        assert len(brush_results) == 1  # Only one brush

    def test_debug_mode_coverage(self, sample_enriched_data):
        """Test debug mode to improve coverage of debug code paths."""
        records = sample_enriched_data["data"]

        # Test all functions with debug=True to hit debug code paths
        matched_records = filter_matched_records(records, debug=True)
        basic_metrics = calculate_basic_metrics(matched_records, debug=True)
        razor_results = aggregate_razors(matched_records, debug=True)
        blade_results = aggregate_blades(matched_records, debug=True)
        soap_results = aggregate_soaps(matched_records, debug=True)
        brush_results = aggregate_brushes(matched_records, debug=True)
        user_results = aggregate_users(matched_records, debug=True)

        # Verify all functions return expected results even with debug=True
        assert len(matched_records) == 5
        assert basic_metrics["total_shaves"] == 5
        assert len(razor_results) == 4
        assert len(blade_results) == 3
        assert len(soap_results) == 4
        assert len(brush_results) == 5
        assert len(user_results) == 4

    def test_error_handling_integration(self):
        """Test error handling with realistic error scenarios."""
        # Test with invalid record types
        with pytest.raises(ValueError, match="Expected list of records"):
            filter_matched_records("invalid")  # type: ignore

        with pytest.raises(ValueError, match="Expected list of records"):
            calculate_basic_metrics("invalid")  # type: ignore

        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_razors("invalid")  # type: ignore

        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_blades("invalid")  # type: ignore

        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_soaps("invalid")  # type: ignore

        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_brushes("invalid")  # type: ignore

        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_users("invalid")  # type: ignore

        # Test with records containing invalid data types
        invalid_records = [
            {
                "id": "test1",
                "author": 123,  # Invalid type
                "created_utc": 1640995200,
                "body": "Test",
            },
            {
                "id": "test2",
                "author": "user2",
                "created_utc": "invalid",  # Invalid type
                "body": "Test",
            },
        ]

        # These should handle invalid data gracefully
        matched_records = filter_matched_records(invalid_records, debug=True)
        assert len(matched_records) == 0

        basic_metrics = calculate_basic_metrics(invalid_records, debug=True)
        assert basic_metrics["total_shaves"] == 1  # One record has valid author
        assert basic_metrics["unique_shavers"] == 1
