"""Tests for brush table generators."""

from sotd.report.table_generators.brush_tables import (
    BrushesTableGenerator,
    BrushHandleMakersTableGenerator,
    BrushKnotMakersTableGenerator,
    BrushFibersTableGenerator,
    BrushKnotSizesTableGenerator,
)


class TestBrushesTableGenerator:
    """Test the BrushesTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BrushesTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brushes": [
                {
                    "name": "Simpson Chubby 2",
                    "shaves": 40,
                    "unique_users": 20,
                },
                {
                    "name": "Declaration B15",
                    "shaves": 25,
                    "unique_users": 12,
                },
            ]
        }
        generator = BrushesTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["name"] == "Simpson Chubby 2"
        assert data[0]["shaves"] == 40

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brushes": [
                {"name": "Simpson Chubby 2"},  # Missing shaves
                {
                    "name": "Declaration B15",
                    "shaves": 25,
                    "unique_users": 12,
                },  # Valid
            ]
        }
        generator = BrushesTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = BrushesTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Brushes"

    def test_column_config(self):
        """Test column configuration."""
        generator = BrushesTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "name" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestBrushHandleMakersTableGenerator:
    """Test the BrushHandleMakersTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BrushHandleMakersTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_handle_makers": [
                {"handle_maker": "Chisel & Hound", "shaves": 60, "unique_users": 30},
                {"handle_maker": "Declaration Grooming", "shaves": 45, "unique_users": 25},
            ]
        }
        generator = BrushHandleMakersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["handle_maker"] == "Chisel & Hound"
        assert data[0]["shaves"] == 60

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_handle_makers": [
                {"handle_maker": "Chisel & Hound"},  # Missing shaves
                {"handle_maker": "Declaration Grooming", "shaves": 45, "unique_users": 25},  # Valid
            ]
        }
        generator = BrushHandleMakersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = BrushHandleMakersTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Brush Handle Makers"

    def test_column_config(self):
        """Test column configuration."""
        generator = BrushHandleMakersTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "handle_maker" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestBrushKnotMakersTableGenerator:
    """Test the BrushKnotMakersTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BrushKnotMakersTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_knot_makers": [
                {"brand": "Declaration Grooming", "shaves": 50, "unique_users": 25},
                {"brand": "AP Shave Co", "shaves": 35, "unique_users": 18},
            ]
        }
        generator = BrushKnotMakersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["brand"] == "Declaration Grooming"
        assert data[0]["shaves"] == 50

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_knot_makers": [
                {"brand": "Declaration Grooming"},  # Missing shaves
                {"brand": "AP Shave Co", "shaves": 35, "unique_users": 18},  # Valid
            ]
        }
        generator = BrushKnotMakersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = BrushKnotMakersTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Brush Knot Makers"

    def test_column_config(self):
        """Test column configuration."""
        generator = BrushKnotMakersTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "brand" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestBrushFibersTableGenerator:
    """Test the BrushFibersTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BrushFibersTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_fibers": [
                {"fiber": "Synthetic", "shaves": 80, "unique_users": 40},
                {"fiber": "Badger", "shaves": 60, "unique_users": 30},
            ]
        }
        generator = BrushFibersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["fiber"] == "Synthetic"
        assert data[0]["shaves"] == 80

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_fibers": [
                {"fiber": "Synthetic"},  # Missing shaves
                {"fiber": "Badger", "shaves": 60, "unique_users": 30},  # Valid
            ]
        }
        generator = BrushFibersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = BrushFibersTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Knot Fibers"

    def test_column_config(self):
        """Test column configuration."""
        generator = BrushFibersTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "fiber" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestBrushKnotSizesTableGenerator:
    """Test the BrushKnotSizesTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BrushKnotSizesTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_knot_sizes": [
                {"knot_size_mm": 26, "shaves": 45, "unique_users": 22},
                {"knot_size_mm": 28, "shaves": 35, "unique_users": 18},
            ]
        }
        generator = BrushKnotSizesTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["knot_size_mm"] == 26
        assert data[0]["shaves"] == 45

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_knot_sizes": [
                {"knot_size_mm": 26},  # Missing shaves
                {"knot_size_mm": 28, "shaves": 35, "unique_users": 18},  # Valid
            ]
        }
        generator = BrushKnotSizesTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = BrushKnotSizesTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Brush Knot Sizes"

    def test_column_config(self):
        """Test column configuration."""
        generator = BrushKnotSizesTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "knot_size_mm" in config
        assert "shaves" in config
        assert "unique_users" in config
