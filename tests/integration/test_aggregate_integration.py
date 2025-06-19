"""Integration tests for the aggregate phase using realistic data."""

import json
import tempfile
from pathlib import Path

import pytest

from sotd.aggregate.aggregation_functions import (
    calculate_basic_metrics,
    filter_matched_records,
)
from sotd.aggregate.product_aggregators import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)
from sotd.aggregate.user_aggregators import (
    aggregate_users,
    aggregate_user_blade_usage,
)
from sotd.aggregate.engine import (
    aggregate_blackbird_plates,
    aggregate_christopher_bradley_plates,
    aggregate_game_changer_plates,
    aggregate_super_speed_tips,
    aggregate_straight_razor_specs,
    aggregate_razor_blade_combinations,
)
from sotd.aggregate.load import load_enriched_data


class TestAggregateIntegration:
    """Integration tests for the aggregate phase."""

    @pytest.fixture
    def sample_enriched_data(self):
        """Sample enriched data for testing,
        including specialized fields for all new aggregations."""
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
                        "Razor: Karve Christopher Bradley\n"
                        "Blade: Feather\n"
                        "Brush: Simpson Chubby 2\n"
                        "Soap: Declaration Grooming"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Karve",
                            "model": "Christopher Bradley",
                            "format": "DE",
                            "match_type": "exact",
                        },
                    },
                    "blade": {
                        "matched": {
                            "brand": "Feather",
                            "model": "Hi-Stainless",
                            "match_type": "exact",
                        },
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
                    "enriched": {
                        "razor": {"plate_level": "C", "plate_type": "SB"},
                        "blade": {"use_count": 3},
                    },
                },
                {
                    "id": "test2",
                    "author": "user2",
                    "created_utc": 1640995201,
                    "body": (
                        "Razor: Merkur 34C\nBlade: Astra SP\n"
                        "Brush: Elite handle w/ Declaration knot\n"
                        "Soap: Barrister and Mann"
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
                        },
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
                    "enriched": {
                        "blade": {"use_count": 2},
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
                        },
                    },
                    "blade": {
                        "matched": {
                            "brand": "Feather",
                            "model": "Hi-Stainless",
                            "match_type": "exact",
                        },
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
                    "enriched": {
                        "razor": {"plate_level": "D", "plate_type": "SB"},
                        "blade": {"use_count": 2},
                    },
                },
                {
                    "id": "test4",
                    "author": "user3",
                    "created_utc": 1640995203,
                    "body": (
                        "Razor: Gillette Super Speed (Red Tip)\nBlade: Personna\n"
                        "Brush: Omega\nSoap: Stirling"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Gillette",
                            "model": "Super Speed",
                            "format": "DE",
                            "match_type": "exact",
                        },
                    },
                    "blade": {
                        "matched": {
                            "brand": "Personna",
                            "model": "Comfort Coated",
                            "match_type": "exact",
                        },
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
                    "enriched": {
                        "razor": {"super_speed_tip": "Red"},
                        "blade": {"use_count": 1},
                    },
                },
                {
                    "id": "test5",
                    "author": "user4",
                    "created_utc": 1640995204,
                    "body": (
                        "Razor: Blackland Blackbird\nBlade: Feather\n"
                        "Brush: Zenith\nSoap: Declaration Grooming"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Blackland",
                            "model": "Blackbird",
                            "format": "DE",
                            "match_type": "exact",
                        },
                    },
                    "blade": {
                        "matched": {
                            "brand": "Feather",
                            "model": "Hi-Stainless",
                            "match_type": "exact",
                        },
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
                    "enriched": {
                        "razor": {"plate": "OC"},
                        "blade": {"use_count": 1},
                    },
                },
                {
                    "id": "test6",
                    "author": "user5",
                    "created_utc": 1640995205,
                    "body": (
                        "Razor: RazoRock Game Changer .84-P\nBlade: Gillette Silver Blue\n"
                        "Brush: Omega\nSoap: Stirling"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "RazoRock",
                            "model": "Game Changer .84-P",
                            "format": "DE",
                            "match_type": "exact",
                        },
                    },
                    "blade": {
                        "matched": {
                            "brand": "Gillette",
                            "model": "Silver Blue",
                            "match_type": "exact",
                        },
                    },
                    "brush": {
                        "matched": {
                            "brand": "Omega",
                            "model": "10066",
                            "handle_maker": "Omega",
                            "fiber": "Boar",
                            "knot_size_mm": 24,
                            "match_type": "exact",
                        }
                    },
                    "soap": {
                        "matched": {
                            "maker": "Stirling",
                            "scent": "Barbershop",
                            "match_type": "exact",
                        }
                    },
                    "enriched": {
                        "razor": {"gap": ".84", "variant": "P"},
                        "blade": {"use_count": 2},
                    },
                },
                {
                    "id": "test7",
                    "author": "user6",
                    "created_utc": 1640995206,
                    "body": (
                        "Razor: Dovo Straight Razor\nBlade: N/A\n" "Brush: Semogue\nSoap: Tabac"
                    ),
                    "razor": {
                        "matched": {
                            "brand": "Dovo",
                            "model": "Best Quality",
                            "format": "Straight",
                            "match_type": "exact",
                        },
                    },
                    "blade": {"matched": {}, "enriched": {}},
                    "brush": {
                        "matched": {
                            "brand": "Semogue",
                            "model": "1305",
                            "handle_maker": "Semogue",
                            "fiber": "Boar",
                            "knot_size_mm": 22,
                            "match_type": "exact",
                        }
                    },
                    "soap": {
                        "matched": {
                            "maker": "Tabac",
                            "scent": "Original",
                            "match_type": "exact",
                        }
                    },
                    "enriched": {
                        "razor": {
                            "grind": "Full Hollow",
                            "width": "5/8",
                            "point": "Round",
                        },
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
        assert len(matched_records) == 7  # All records should be matched

        # Test basic metrics calculation
        basic_metrics = calculate_basic_metrics(matched_records, debug=True)
        assert basic_metrics["total_shaves"] == 7
        assert basic_metrics["unique_shavers"] == 6
        assert basic_metrics["avg_shaves_per_user"] == pytest.approx(1.166, 0.01)

        # Test razor aggregation
        razor_results = aggregate_razors(matched_records, debug=True)
        assert len(razor_results) == 6  # 6 unique razors

        # Check Karve Christopher Bradley (used twice by user1)
        karve_result = next(r for r in razor_results if "Karve Christopher Bradley" in r["name"])
        assert karve_result["shaves"] == 2
        assert karve_result["unique_users"] == 1
        assert karve_result["avg_shaves_per_user"] == 2.0

        # Test blade aggregation
        blade_results = aggregate_blades(matched_records, debug=True)
        assert len(blade_results) == 4  # 4 unique blade brands (Feather, Astra, Personna, Gillette)

        # Check Feather (used 3 times by 2 users)
        feather_result = next(r for r in blade_results if "Feather" in r["name"])
        assert feather_result["shaves"] == 3
        assert feather_result["unique_users"] == 2
        assert feather_result["avg_shaves_per_user"] == 1.5

        # Test soap aggregation
        soap_results = aggregate_soaps(matched_records, debug=True)
        assert len(soap_results) == 6  # 6 unique soaps

        # Check Declaration Grooming Sellout (used 2 times by user1)
        dg_result = next(r for r in soap_results if "Declaration Grooming Sellout" in r["name"])
        assert dg_result["shaves"] == 2
        assert dg_result["unique_users"] == 1
        assert dg_result["avg_shaves_per_user"] == 2.0

        # Test brush aggregation
        brush_results = aggregate_brushes(matched_records, debug=True)
        assert len(brush_results) == 7  # 7 unique brushes

        # Test user aggregation
        user_results = aggregate_users(matched_records, debug=True)
        assert len(user_results) == 6  # 6 unique users

        # Check user1 (2 shaves)
        user1_result = next(r for r in user_results if r["user"] == "user1")
        assert user1_result["shaves"] == 2
        assert user1_result["avg_shaves_per_user"] == 1.0

        # --- New specialized aggregations ---
        blackbird_plates = aggregate_blackbird_plates(matched_records, debug=True)
        christopher_bradley_plates = aggregate_christopher_bradley_plates(
            matched_records, debug=True
        )
        game_changer_plates = aggregate_game_changer_plates(matched_records, debug=True)
        super_speed_tips = aggregate_super_speed_tips(matched_records, debug=True)
        straight_razor_specs = aggregate_straight_razor_specs(matched_records, debug=True)
        razor_blade_combinations = aggregate_razor_blade_combinations(matched_records, debug=True)
        user_blade_usage = aggregate_user_blade_usage(matched_records, debug=True)

        # Assert that all new categories return lists (may be empty for this sample)
        assert isinstance(blackbird_plates, list)
        assert isinstance(christopher_bradley_plates, list)
        assert isinstance(game_changer_plates, list)
        assert isinstance(super_speed_tips, list)
        assert isinstance(straight_razor_specs, list)
        assert isinstance(razor_blade_combinations, list)
        assert isinstance(user_blade_usage, list)

        # For this sample, Blackbird Plates should have 1 entry (user4)
        assert len(blackbird_plates) == 1
        # Christopher Bradley Plates should have 2 entries (C SB and D SB plates)
        assert len(christopher_bradley_plates) == 2
        # Game Changer Plates should have 1 entry (user5 with Gap .84 P)
        assert len(game_changer_plates) == 1
        # Super Speed Tips should have 1 entry (user6)
        assert len(super_speed_tips) == 1
        # Straight Razor Specs should have 1 entry (user7)
        assert len(straight_razor_specs) == 1
        # Razor-Blade Combinations: at least 4 unique combos
        assert len(razor_blade_combinations) >= 4
        # User Blade Usage: at least 3 users (since 3 unique blades)
        assert len(user_blade_usage) >= 3

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
            assert len(records) == 7

            # Process data using the real pipeline logic
            matched_records = filter_matched_records(records, debug=True)
            assert len(matched_records) == 7

            # Use the real process_month function to ensure output structure consistency
            from sotd.aggregate.run import process_month
            import argparse

            # Create mock args for process_month
            mock_args = argparse.Namespace(out_dir=str(temp_dir), force=False, debug=True)

            # Process the month using the real pipeline
            results = process_month(2025, 1, mock_args)
            assert results["status"] == "success"

            # Verify the aggregated file was created
            aggregated_file = Path(temp_dir) / "aggregated" / "2025-01.json"
            assert aggregated_file.exists()

            # Load and verify the saved data structure
            with aggregated_file.open("r") as f:
                saved_data = json.load(f)

            # Verify metadata
            assert "meta" in saved_data
            assert "data" in saved_data
            assert saved_data["meta"]["month"] == "2025-01"
            assert saved_data["meta"]["total_shaves"] == 7
            assert saved_data["meta"]["unique_shavers"] == 6

            # Verify core categories
            assert len(saved_data["data"]["razors"]) == 6
            assert len(saved_data["data"]["blades"]) == 4
            assert len(saved_data["data"]["soaps"]) == 6
            assert len(saved_data["data"]["brushes"]) == 7
            assert len(saved_data["data"]["users"]) == 6

            # Verify new specialized categories are present
            assert "blackbird_plates" in saved_data["data"]
            assert "christopher_bradley_plates" in saved_data["data"]
            assert "game_changer_plates" in saved_data["data"]
            assert "super_speed_tips" in saved_data["data"]
            assert "straight_razor_specs" in saved_data["data"]
            assert "razor_blade_combinations" in saved_data["data"]
            assert "user_blade_usage" in saved_data["data"]

            # Verify counts for new categories
            assert len(saved_data["data"]["blackbird_plates"]) == 1
            assert len(saved_data["data"]["christopher_bradley_plates"]) == 2  # C and D plates
            assert len(saved_data["data"]["game_changer_plates"]) == 1
            assert len(saved_data["data"]["super_speed_tips"]) == 1
            assert len(saved_data["data"]["straight_razor_specs"]) == 1
            assert len(saved_data["data"]["razor_blade_combinations"]) >= 5
            assert len(saved_data["data"]["user_blade_usage"]) >= 5

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
        basic_metrics = calculate_basic_metrics(edge_case_records, debug=True)
        assert basic_metrics["total_shaves"] == 5
        assert basic_metrics["unique_shavers"] == 5
        assert basic_metrics["avg_shaves_per_user"] == 1.0

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
        assert len(matched_records) == 7
        assert basic_metrics["total_shaves"] == 7
        assert len(razor_results) == 6
        assert len(blade_results) == 4
        assert len(soap_results) == 6
        assert len(brush_results) == 7
        assert len(user_results) == 6

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
