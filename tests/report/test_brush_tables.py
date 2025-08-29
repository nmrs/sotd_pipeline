"""Tests for brush table generators."""

from sotd.report.table_generators.table_generator import TableGenerator


class TestBrushesTableGenerator:
    """Test the BrushesTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brushes")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 40, "unique_users": 20},
                {"name": "Declaration B15", "shaves": 25, "unique_users": 12},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brushes")
        assert "Simpson Chubby 2" in data
        assert "40" in data
        assert "Declaration B15" in data
        assert "25" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brushes": [
                {"name": "Simpson Chubby 2"},  # Missing shaves
                {"name": "Declaration B15", "shaves": 25, "unique_users": 12},  # Valid
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brushes")
        # Should still generate table with available data
        assert "Declaration B15" in data

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "brushes" in generator.get_available_table_names()
        assert "brush_handle_makers" in generator.get_available_table_names()
        assert "brush_knot_makers" in generator.get_available_table_names()
        assert "brush_fibers" in generator.get_available_table_names()
        assert "brush_knot_sizes" in generator.get_available_table_names()


class TestBrushHandleMakersTableGenerator:
    """Test the BrushHandleMakersTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-handle-makers")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_handle_makers": [
                {"rank": 1, "name": "Declaration", "shaves": 40, "unique_users": 20},
                {"rank": 2, "name": "Simpson", "shaves": 25, "unique_users": 12},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-handle-makers")
        assert "Declaration" in data
        assert "Simpson" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_handle_makers": [
                {"name": "Declaration", "shaves": 40},  # Missing rank
                {"rank": 2, "shaves": 25},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-handle-makers")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "brushes" in generator.get_available_table_names()
        assert "brush_handle_makers" in generator.get_available_table_names()
        assert "brush_knot_makers" in generator.get_available_table_names()
        assert "brush_fibers" in generator.get_available_table_names()
        assert "brush_knot_sizes" in generator.get_available_table_names()


class TestBrushKnotMakersTableGenerator:
    """Test the BrushKnotMakersTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-knot-makers")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_knot_makers": [
                {"rank": 1, "name": "Declaration", "shaves": 40, "unique_users": 20},
                {"rank": 2, "name": "Simpson", "shaves": 25, "unique_users": 12},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-knot-makers")
        assert "Declaration" in data
        assert "Simpson" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_knot_makers": [
                {"name": "Declaration", "shaves": 40},  # Missing rank
                {"rank": 2, "shaves": 25},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-knot-makers")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "brushes" in generator.get_available_table_names()
        assert "brush_handle_makers" in generator.get_available_table_names()
        assert "brush_knot_makers" in generator.get_available_table_names()
        assert "brush_fibers" in generator.get_available_table_names()
        assert "brush_knot_sizes" in generator.get_available_table_names()


class TestBrushFibersTableGenerator:
    """Test the BrushFibersTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-fibers")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_fibers": [
                {"rank": 1, "name": "Badger", "shaves": 40, "unique_users": 20},
                {"rank": 2, "name": "Synthetic", "shaves": 25, "unique_users": 12},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-fibers")
        assert "Badger" in data
        assert "Synthetic" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_fibers": [
                {"name": "Badger", "shaves": 40},  # Missing rank
                {"rank": 2, "shaves": 25},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-fibers")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "brushes" in generator.get_available_table_names()
        assert "brush_handle_makers" in generator.get_available_table_names()
        assert "brush_knot_makers" in generator.get_available_table_names()
        assert "brush_fibers" in generator.get_available_table_names()
        assert "brush_knot_sizes" in generator.get_available_table_names()


class TestBrushKnotSizesTableGenerator:
    """Test the BrushKnotSizesTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-knot-sizes")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brush_knot_sizes": [
                {"rank": 1, "name": "24mm", "shaves": 40, "unique_users": 20},
                {"rank": 2, "name": "26mm", "shaves": 25, "unique_users": 12},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-knot-sizes")
        assert "24mm" in data
        assert "26mm" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brush_knot_sizes": [
                {"name": "24mm", "shaves": 40},  # Missing rank
                {"rank": 2, "shaves": 25},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("brush-knot-sizes")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {
            "brushes": [],
            "brush_handle_makers": [],
            "brush_knot_makers": [],
            "brush_fibers": [],
            "brush_knot_sizes": [],
        }
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "brushes" in generator.get_available_table_names()
        assert "brush_handle_makers" in generator.get_available_table_names()
        assert "brush_knot_makers" in generator.get_available_table_names()
        assert "brush_fibers" in generator.get_available_table_names()
        assert "brush_knot_sizes" in generator.get_available_table_names()
