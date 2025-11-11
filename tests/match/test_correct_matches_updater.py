"""Test correct matches updater for managing correct_matches.yaml file operations."""

import shutil
import tempfile
from pathlib import Path

import yaml

from sotd.match.correct_matches_updater import CorrectMatchesUpdater


class TestCorrectMatchesUpdater:
    """Test CorrectMatchesUpdater functionality."""

    def setup_method(self):
        """Set up test directory."""
        self.test_dir = tempfile.mkdtemp()
        self.correct_matches_path = Path(self.test_dir) / "correct_matches"
        self.updater = CorrectMatchesUpdater(self.correct_matches_path)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        # Create a temporary updater to test the default path behavior
        # without actually using the production file
        temp_path = Path(self.test_dir) / "default_test"
        updater = CorrectMatchesUpdater(temp_path)
        # Test that the path is set correctly
        assert updater.correct_matches_path == temp_path

    def test_init_with_custom_path(self):
        """Test initialization with custom path."""
        custom_path = Path(self.test_dir) / "custom" / "path" / "correct_matches"
        updater = CorrectMatchesUpdater(custom_path)
        assert updater.correct_matches_path == custom_path

    def test_ensure_directory_exists(self):
        """Test directory creation."""
        # Create updater with nested directory path
        nested_path = Path(self.test_dir) / "nested" / "deep" / "correct_matches"
        CorrectMatchesUpdater(nested_path)

        # Directory should be created
        assert nested_path.exists()
        assert nested_path.is_dir()

    def test_load_correct_matches_empty_file(self):
        """Test loading from non-existent file."""
        data = self.updater.load_correct_matches()
        assert data == {}

    def test_load_correct_matches_existing_file(self):
        """Test loading from existing file."""
        # Create test data
        test_data = {"brush": {"Test Brand": {"Test Model": ["test pattern"]}}}

        # Write to brush.yaml file within the directory
        brush_file = self.correct_matches_path / "brush.yaml"
        with open(brush_file, "w") as f:
            yaml.dump(test_data["brush"], f)

        # Load data
        data = self.updater.load_correct_matches()
        assert data == test_data

    def test_load_correct_matches_corrupted_file(self):
        """Test loading from corrupted YAML file."""
        # Create corrupted YAML in brush.yaml file
        brush_file = self.correct_matches_path / "brush.yaml"
        with open(brush_file, "w") as f:
            f.write("invalid: yaml: content: [")

        # Should return empty dict (corrupted files are skipped)
        data = self.updater.load_correct_matches()
        assert data == {}

    def test_add_or_update_entry_brush_field(self):
        """Test adding brush field entry."""
        result_data = {"brand": "Test Brand", "model": "Test Model"}

        self.updater.add_or_update_entry("test brush input", result_data, "validated", "brush")

        # Verify entry was added
        data = self.updater.load_correct_matches()
        assert "brush" in data
        assert "Test Brand" in data["brush"]
        assert "Test Model" in data["brush"]["Test Brand"]
        assert "test brush input" in data["brush"]["Test Brand"]["Test Model"]

    def test_add_or_update_entry_handle_field(self):
        """Test adding handle field entry."""
        result_data = {"handle_maker": "Test Handle Maker", "handle_model": "Test Handle Model"}

        self.updater.add_or_update_entry("test handle input", result_data, "validated", "handle")

        # Verify entry was added
        data = self.updater.load_correct_matches()
        assert "handle" in data
        assert "test handle input" in data["handle"]
        assert data["handle"]["test handle input"] == result_data

    def test_add_or_update_entry_knot_field(self):
        """Test adding knot field entry."""
        result_data = {"brand": "Test Knot Brand", "model": "Test Knot Model", "fiber": "badger"}

        self.updater.add_or_update_entry("test knot input", result_data, "validated", "knot")

        # Verify entry was added
        data = self.updater.load_correct_matches()
        assert "knot" in data
        assert "test knot input" in data["knot"]
        assert data["knot"]["test knot input"] == result_data

    def test_add_or_update_entry_split_brush_field(self):
        """Test adding split_brush field entry."""
        result_data = {"handle": "test handle", "knot": "test knot"}

        self.updater.add_or_update_entry(
            "test split brush input", result_data, "validated", "split_brush"
        )

        # Verify entry was added to handle and knot sections
        data = self.updater.load_correct_matches()
        assert "handle" in data
        assert "knot" in data
        assert "Unknown" in data["handle"]
        assert "test handle" in data["handle"]["Unknown"]
        assert "test split brush input" in data["handle"]["Unknown"]["test handle"]
        assert "Unknown" in data["knot"]
        assert "test knot" in data["knot"]["Unknown"]
        assert "test split brush input" in data["knot"]["Unknown"]["test knot"]

    def test_add_or_update_entry_case_insensitive(self):
        """Test that input text preserves original casing."""
        result_data = {"brand": "Test Brand", "model": "Test Model"}

        self.updater.add_or_update_entry("TEST BRUSH INPUT", result_data, "validated", "brush")

        # Verify entry was added with original casing preserved
        data = self.updater.load_correct_matches()
        assert "TEST BRUSH INPUT" in data["brush"]["Test Brand"]["Test Model"]

    def test_add_or_update_entry_duplicate_brush(self):
        """Test adding duplicate brush entry."""
        result_data = {"brand": "Test Brand", "model": "Test Model"}

        # Add first entry
        self.updater.add_or_update_entry("test brush input", result_data, "validated", "brush")

        # Add duplicate entry
        self.updater.add_or_update_entry("test brush input", result_data, "validated", "brush")

        # Verify only one entry exists
        data = self.updater.load_correct_matches()
        patterns = data["brush"]["Test Brand"]["Test Model"]
        assert len(patterns) == 1
        assert "test brush input" in patterns

    def test_save_correct_matches_atomic_write(self):
        """Test atomic write operations."""
        test_data = {"brush": {"Test Brand": {"Test Model": ["test pattern"]}}}

        # Save data
        self.updater.save_correct_matches(test_data)

        # Verify directory exists
        assert self.correct_matches_path.exists()
        assert self.correct_matches_path.is_dir()

        # Verify brush.yaml file was created
        brush_file = self.correct_matches_path / "brush.yaml"
        assert brush_file.exists()

        # Verify content
        with open(brush_file, "r") as f:
            loaded_data = yaml.safe_load(f)
        assert loaded_data == test_data["brush"]

    def test_remove_entry_brush_field(self):
        """Test removing brush field entry."""
        # Add entry first
        result_data = {"brand": "Test Brand", "model": "Test Model"}
        self.updater.add_or_update_entry("test brush input", result_data, "validated", "brush")

        # Remove entry
        removed = self.updater.remove_entry("test brush input", "brush")
        assert removed is True

        # Verify entry was removed
        data = self.updater.load_correct_matches()
        assert "brush" not in data or not data["brush"]

    def test_remove_entry_handle_field(self):
        """Test removing handle field entry."""
        # Add entry first
        result_data = {"handle_maker": "Test Handle Maker", "handle_model": "Test Handle Model"}
        self.updater.add_or_update_entry("test handle input", result_data, "validated", "handle")

        # Remove entry
        removed = self.updater.remove_entry("test handle input", "handle")
        assert removed is True

        # Verify entry was removed
        data = self.updater.load_correct_matches()
        assert "handle" not in data or "test handle input" not in data["handle"]

    def test_remove_entry_not_found(self):
        """Test removing non-existent entry."""
        removed = self.updater.remove_entry("non-existent", "brush")
        assert removed is False

    def test_get_entry_brush_field(self):
        """Test getting brush field entry."""
        # Add entry first
        result_data = {"brand": "Test Brand", "model": "Test Model"}
        self.updater.add_or_update_entry("test brush input", result_data, "validated", "brush")

        # Get entry
        entry = self.updater.get_entry("test brush input", "brush")
        assert entry is not None
        assert entry["brand"] == "Test Brand"
        assert entry["model"] == "Test Model"
        assert entry["pattern"] == "test brush input"

    def test_get_entry_handle_field(self):
        """Test getting handle field entry."""
        # Add entry first
        result_data = {"handle_maker": "Test Handle Maker", "handle_model": "Test Handle Model"}
        self.updater.add_or_update_entry("test handle input", result_data, "validated", "handle")

        # Get entry
        entry = self.updater.get_entry("test handle input", "handle")
        assert entry is not None
        assert entry["handle_maker"] == "Test Handle Maker"
        assert entry["handle_model"] == "Test Handle Model"

    def test_get_entry_not_found(self):
        """Test getting non-existent entry."""
        entry = self.updater.get_entry("non-existent", "brush")
        assert entry is None

    def test_has_entry_true(self):
        """Test has_entry returns True for existing entry."""
        # Add entry first
        result_data = {"brand": "Test Brand", "model": "Test Model"}
        self.updater.add_or_update_entry("test brush input", result_data, "validated", "brush")

        # Check if entry exists
        exists = self.updater.has_entry("test brush input", "brush")
        assert exists is True

    def test_has_entry_false(self):
        """Test has_entry returns False for non-existent entry."""
        exists = self.updater.has_entry("non-existent", "brush")
        assert exists is False

    def test_update_existing_entry(self):
        """Test updating existing entry."""
        # Add initial entry
        initial_data = {"brand": "Test Brand", "model": "Test Model"}
        self.updater.add_or_update_entry("test brush input", initial_data, "validated", "brush")

        # Update with new data
        updated_data = {"brand": "Updated Brand", "model": "Updated Model"}
        self.updater.add_or_update_entry("test brush input", updated_data, "overridden", "brush")

        # Verify entry was updated
        data = self.updater.load_correct_matches()
        assert "Updated Brand" in data["brush"]
        assert "Updated Model" in data["brush"]["Updated Brand"]
        assert "test brush input" in data["brush"]["Updated Brand"]["Updated Model"]
