"""Integration tests for the aggregate phase."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sotd.aggregate.cli import main
from sotd.aggregate.engine import process_months
from sotd.aggregate.load import load_enriched_data
from sotd.aggregate.processor import aggregate_all
from sotd.aggregate.save import save_aggregated_data


class TestAggregateIntegration:
    """Integration tests for the aggregate phase."""

    @pytest.fixture
    def sample_enriched_data(self):
        """Sample enriched data for testing."""
        return [
            {
                "id": "test1",
                "author": "user1",
                "created_utc": 1640995200,
                "thread_title": "SOTD Thread - Jan 01, 2025",
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
                    "enriched": {"plate_level": "C", "plate_type": "SB"},
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "format": "DE",
                        "match_type": "exact",
                    },
                    "enriched": {"use_count": 3},
                },
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "handle": {"brand": "Simpson", "model": "Chubby 2"},
                        "knot": {
                            "brand": "Simpson",
                            "model": "Chubby 2",
                            "fiber": "Badger",
                            "knot_size_mm": 27,
                        },
                        "match_type": "exact",
                    }
                },
                "soap": {
                    "matched": {
                        "brand": "Declaration Grooming",
                        "scent": "Sellout",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test2",
                "author": "user2",
                "created_utc": 1640995201,
                "thread_title": "SOTD Thread - Jan 01, 2025",
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
                        "format": "DE",
                        "match_type": "exact",
                    },
                    "enriched": {"use_count": 2},
                },
                "brush": {
                    "matched": {
                        "brand": "Declaration Grooming",
                        "model": "B15",
                        "handle": {"brand": "Elite", "model": None},
                        "knot": {
                            "brand": "Declaration Grooming",
                            "model": "B15",
                            "fiber": "Badger",
                            "knot_size_mm": 26,
                        },
                        "match_type": "exact",
                    }
                },
                "soap": {
                    "matched": {
                        "brand": "Barrister and Mann",
                        "scent": "Seville",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test3",
                "author": "user1",  # Same user as test1
                "created_utc": 1640995202,
                "thread_title": "SOTD Thread - Jan 02, 2025",
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
                    "enriched": {"plate_level": "D", "plate_type": "SB"},
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "format": "DE",
                        "match_type": "exact",
                    },
                    "enriched": {"use_count": 2},
                },
                "brush": {
                    "matched": {
                        "brand": "Stirling",
                        "model": "Badger",
                        "handle": {"brand": "Stirling", "model": "Badger"},
                        "knot": {
                            "brand": "Stirling",
                            "model": "Badger",
                            "fiber": "Badger",
                            "knot_size_mm": 24,
                        },
                        "match_type": "exact",
                    }
                },
                "soap": {
                    "matched": {
                        "brand": "Declaration Grooming",
                        "scent": "Sellout",
                        "match_type": "exact",
                    }
                },
            },
        ]

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            enriched_dir = data_dir / "enriched"
            enriched_dir.mkdir()
            aggregated_dir = data_dir / "aggregated"
            aggregated_dir.mkdir()
            yield data_dir

    def test_end_to_end_aggregation(self, sample_enriched_data, temp_data_dir):
        """Test complete end-to-end aggregation process."""
        # Write sample enriched data
        enriched_file = temp_data_dir / "enriched" / "2025-01.json"
        with open(enriched_file, "w") as f:
            json.dump(sample_enriched_data, f, ensure_ascii=False)

        # Process the month
        process_months(["2025-01"], temp_data_dir, debug=True)

        # Verify output file was created
        aggregated_file = temp_data_dir / "aggregated" / "2025-01.json"
        assert aggregated_file.exists()

        # Load and verify aggregated data
        with open(aggregated_file, "r") as f:
            aggregated_data = json.load(f)

        # Check metadata
        assert "meta" in aggregated_data
        assert aggregated_data["meta"]["month"] == "2025-01"
        assert aggregated_data["meta"]["total_shaves"] == 3
        assert aggregated_data["meta"]["unique_shavers"] == 2

        # Check data structure
        assert "data" in aggregated_data
        data = aggregated_data["data"]

        # Verify all required categories are present
        required_categories = [
            "razors",
            "blades",
            "brushes",
            "soaps",
            "razor_manufacturers",
            "blade_manufacturers",
            "soap_makers",
            "razor_formats",
            "brush_handle_makers",
            "brush_knot_makers",
            "brush_fibers",
            "brush_knot_sizes",
            "blackbird_plates",
            "christopher_bradley_plates",
            "game_changer_plates",
            "super_speed_tips",
            "straight_widths",
            "straight_grinds",
            "straight_points",
            "users",
            "razor_blade_combinations",
            "highest_use_count_per_blade",
        ]

        for category in required_categories:
            assert category in data, f"Missing category: {category}"
            assert isinstance(data[category], list), f"Category {category} should be a list"

        # Verify specific aggregations
        assert len(data["razors"]) > 0
        assert len(data["blades"]) > 0
        assert len(data["brushes"]) > 0
        assert len(data["soaps"]) > 0
        assert len(data["users"]) > 0

        # Verify rank fields are present for list categories with dictionaries
        for category in data:
            if isinstance(data[category], list) and data[category]:
                # Check if the first item is a dictionary (indicating it's an aggregation result)
                first_item = data[category][0]
                if isinstance(first_item, dict):
                    for item in data[category]:
                        assert "rank" in item, f"Missing rank in {category}"
                        assert isinstance(
                            item["rank"], int
                        ), f"Rank should be integer in {category}"
                        assert item["rank"] >= 1, f"Rank should be positive in {category}"

    def test_file_io_integration(self, sample_enriched_data, temp_data_dir):
        """Test file I/O operations with sample data."""
        # Test loading enriched data
        enriched_file = temp_data_dir / "enriched" / "2025-01.json"
        with open(enriched_file, "w") as f:
            json.dump(sample_enriched_data, f, ensure_ascii=False)

        records = load_enriched_data("2025-01", temp_data_dir)
        assert len(records) == 3

        # Test aggregation
        aggregated_data = aggregate_all(records, "2025-01")
        assert "meta" in aggregated_data
        assert "data" in aggregated_data

        # Test saving aggregated data
        save_aggregated_data(aggregated_data, "2025-01", temp_data_dir)
        aggregated_file = temp_data_dir / "aggregated" / "2025-01.json"
        assert aggregated_file.exists()

        # Verify saved data can be loaded
        with open(aggregated_file, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data["meta"]["month"] == "2025-01"

    def test_cli_interface(self, sample_enriched_data, temp_data_dir):
        """Test CLI interface with various arguments."""
        # Write sample data
        enriched_file = temp_data_dir / "enriched" / "2025-01.json"
        with open(enriched_file, "w") as f:
            json.dump(sample_enriched_data, f, ensure_ascii=False)

        # Test single month processing
        with patch(
            "sys.argv", ["aggregate", "--month", "2025-01", "--data-dir", str(temp_data_dir)]
        ):
            main()

        aggregated_file = temp_data_dir / "aggregated" / "2025-01.json"
        assert aggregated_file.exists()

    def test_error_handling_integration(self, temp_data_dir):
        """Test error handling scenarios."""
        # Test missing enriched file
        with pytest.raises(FileNotFoundError):
            load_enriched_data("2025-01", temp_data_dir)

        # Test invalid data structure
        invalid_data = {"invalid": "structure"}
        enriched_file = temp_data_dir / "enriched" / "2025-01.json"
        with open(enriched_file, "w") as f:
            json.dump(invalid_data, f, ensure_ascii=False)

        with pytest.raises(ValueError, match="Expected a list of records"):
            load_enriched_data("2025-01", temp_data_dir)

    def test_edge_cases_with_realistic_data(self, temp_data_dir):
        """Test edge cases with realistic data."""
        # Test empty data
        empty_data = []
        enriched_file = temp_data_dir / "enriched" / "2025-01.json"
        with open(enriched_file, "w") as f:
            json.dump(empty_data, f, ensure_ascii=False)

        records = load_enriched_data("2025-01", temp_data_dir)
        aggregated_data = aggregate_all(records, "2025-01")

        assert aggregated_data["meta"]["total_shaves"] == 0
        assert aggregated_data["meta"]["unique_shavers"] == 0

        # Test single record
        single_record_data = [
            {
                "id": "test1",
                "author": "user1",
                "razor": {"matched": {"brand": "Test", "model": "Test", "format": "DE"}},
                "blade": {"matched": {"brand": "Test", "model": "Test", "format": "DE"}},
                "brush": {
                    "matched": {
                        "brand": "Test",
                        "model": "Test",
                        "handle": {"brand": "Test", "model": "Test"},
                        "knot": {"fiber": "Synthetic"},
                    }
                },
                "soap": {"matched": {"brand": "Test", "scent": "Test"}},
            }
        ]

        with open(enriched_file, "w") as f:
            json.dump(single_record_data, f, ensure_ascii=False)

        records = load_enriched_data("2025-01", temp_data_dir)
        aggregated_data = aggregate_all(records, "2025-01")

        assert aggregated_data["meta"]["total_shaves"] == 1
        assert aggregated_data["meta"]["unique_shavers"] == 1

    def test_debug_mode_coverage(self, sample_enriched_data, temp_data_dir, caplog):
        """Test debug mode provides useful output."""
        enriched_file = temp_data_dir / "enriched" / "2025-01.json"
        with open(enriched_file, "w") as f:
            json.dump(sample_enriched_data, f, ensure_ascii=False)

        with caplog.at_level("DEBUG"):
            process_months(["2025-01"], temp_data_dir, debug=True)

        log_output = caplog.text
        assert "Loaded 3 records for 2025-01" in log_output
        assert "Saved aggregated data for 2025-01" in log_output

    def test_multiple_months_processing(self, sample_enriched_data, temp_data_dir):
        """Test processing multiple months."""
        # Create data for two months
        for month in ["2025-01", "2025-02"]:
            enriched_file = temp_data_dir / "enriched" / f"{month}.json"
            with open(enriched_file, "w") as f:
                json.dump(sample_enriched_data, f, ensure_ascii=False)

        process_months(["2025-01", "2025-02"], temp_data_dir)

        # Verify both files were created
        for month in ["2025-01", "2025-02"]:
            aggregated_file = temp_data_dir / "aggregated" / f"{month}.json"
            assert aggregated_file.exists()
