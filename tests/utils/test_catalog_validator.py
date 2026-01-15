"""Tests for catalog validator module."""

from pathlib import Path

import pytest

from sotd.utils.catalog_validator import validate_patterns_format


class TestValidatePatternsFormat:
    """Test validate_patterns_format function."""

    def test_valid_patterns_list_at_brand_level(self):
        """Test that valid list patterns at brand level pass validation."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Brand1": {
                "patterns": ["pattern1", "pattern2"],
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_valid_patterns_list_at_model_level(self):
        """Test that valid list patterns at model level pass validation."""
        catalog_path = Path("data/razors.yaml")
        data = {
            "Brand1": {
                "Model1": {
                    "patterns": ["pattern1", "pattern2"],
                }
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_valid_patterns_list_at_scent_level(self):
        """Test that valid list patterns at scent level pass validation."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Brand1": {
                "scents": {
                    "Scent1": {
                        "patterns": ["pattern1", "pattern2"],
                    }
                }
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_valid_patterns_list_at_format_level(self):
        """Test that valid list patterns at format level (blades) pass validation."""
        catalog_path = Path("data/blades.yaml")
        data = {
            "DE": {
                "Brand1": {
                    "Model1": {
                        "patterns": ["pattern1", "pattern2"],
                    }
                }
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_valid_empty_patterns_list(self):
        """Test that empty patterns list passes validation."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Brand1": {
                "patterns": [],
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_invalid_patterns_string_at_brand_level(self):
        """Test that string patterns at brand level raise ValueError."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Brand1": {
                "patterns": "pattern1",  # Missing '-' prefix, treated as string
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        assert "Invalid patterns format" in str(exc_info.value)
        assert "Brand1 -> patterns" in str(exc_info.value)
        assert "Expected: list" in str(exc_info.value)
        assert "Got: str" in str(exc_info.value)

    def test_invalid_patterns_string_at_model_level(self):
        """Test that string patterns at model level raise ValueError."""
        catalog_path = Path("data/razors.yaml")
        data = {
            "Brand1": {
                "Model1": {
                    "patterns": "pattern1",  # Missing '-' prefix
                }
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        assert "Invalid patterns format" in str(exc_info.value)
        assert "Brand1 -> Model1 -> patterns" in str(exc_info.value)

    def test_invalid_patterns_string_at_scent_level(self):
        """Test that string patterns at scent level raise ValueError."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Brand1": {
                "scents": {
                    "Scent1": {
                        "patterns": "pattern1",  # Missing '-' prefix
                    }
                }
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        assert "Invalid patterns format" in str(exc_info.value)
        assert "Brand1 -> scents -> Scent1 -> patterns" in str(exc_info.value)

    def test_invalid_patterns_string_at_format_level(self):
        """Test that string patterns at format level (blades) raise ValueError."""
        catalog_path = Path("data/blades.yaml")
        data = {
            "DE": {
                "Brand1": {
                    "Model1": {
                        "patterns": "pattern1",  # Missing '-' prefix
                    }
                }
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        assert "Invalid patterns format" in str(exc_info.value)
        assert "DE -> Brand1 -> Model1 -> patterns" in str(exc_info.value)

    def test_invalid_patterns_in_multiple_locations(self):
        """Test that validation catches first invalid pattern and raises."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Brand1": {
                "patterns": "pattern1",  # Invalid
                "scents": {
                    "Scent1": {
                        "patterns": ["pattern1"],  # Valid
                    },
                    "Scent2": {
                        "patterns": "pattern2",  # Invalid (but won't be reached)
                    },
                },
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        # Should catch the first error at brand level
        assert "Brand1 -> patterns" in str(exc_info.value)

    def test_valid_patterns_with_other_fields(self):
        """Test that validation works correctly when other fields are present."""
        catalog_path = Path("data/razors.yaml")
        data = {
            "Brand1": {
                "Model1": {
                    "format": "DE",
                    "patterns": ["pattern1", "pattern2"],  # Valid
                    "wsdb_slug": "brand1-model1",
                }
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_valid_patterns_in_nested_brush_structure(self):
        """Test that validation works with brush catalog nested structure."""
        catalog_path = Path("data/brushes.yaml")
        data = {
            "known_brushes": {
                "Brand1": {
                    "Model1": {
                        "patterns": ["pattern1", "pattern2"],
                        "fiber": "Badger",
                    }
                }
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_invalid_patterns_in_nested_brush_structure(self):
        """Test that validation catches invalid patterns in brush structure."""
        catalog_path = Path("data/brushes.yaml")
        data = {
            "known_brushes": {
                "Brand1": {
                    "Model1": {
                        "patterns": "pattern1",  # Invalid
                        "fiber": "Badger",
                    }
                }
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        assert "known_brushes -> Brand1 -> Model1 -> patterns" in str(exc_info.value)

    def test_valid_patterns_in_handle_structure(self):
        """Test that validation works with handle catalog structure."""
        catalog_path = Path("data/handles.yaml")
        data = {
            "artisan_handles": {
                "Brand1": {
                    "Model1": {
                        "patterns": ["pattern1"],
                    }
                }
            }
        }
        # Should not raise
        validate_patterns_format(data, catalog_path)

    def test_invalid_patterns_in_handle_structure(self):
        """Test that validation catches invalid patterns in handle structure."""
        catalog_path = Path("data/handles.yaml")
        data = {
            "artisan_handles": {
                "Brand1": {
                    "Model1": {
                        "patterns": "pattern1",  # Invalid
                    }
                }
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        assert "artisan_handles -> Brand1 -> Model1 -> patterns" in str(exc_info.value)

    def test_error_message_includes_fix_example(self):
        """Test that error message includes helpful fix example."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Miraculum": {
                "patterns": "miraculum",  # Invalid
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        error_msg = str(exc_info.value)
        assert "Fix: Change from:" in error_msg
        assert "To:" in error_msg
        assert "- miraculum" in error_msg

    def test_error_message_includes_line_number(self, tmp_path):
        """Test that error message includes line number when available."""
        # Create a temporary YAML file with invalid patterns
        catalog_path = tmp_path / "test.yaml"
        yaml_content = """Brand1:
  patterns:
    pattern1  # Missing '-' prefix
"""
        catalog_path.write_text(yaml_content, encoding="utf-8")

        data = {
            "Brand1": {
                "patterns": "pattern1",  # Invalid
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        error_msg = str(exc_info.value)
        # Should include line number (line 3 where "pattern1" appears)
        assert "line" in error_msg.lower() or "(line" in error_msg

    def test_non_dict_data_does_not_raise(self):
        """Test that non-dict data doesn't cause errors (just returns)."""
        catalog_path = Path("data/soaps.yaml")
        # Should not raise, just return
        validate_patterns_format({}, catalog_path)
        # Empty dict should be fine
        validate_patterns_format({"Brand1": {}}, catalog_path)

    def test_nested_lists_with_dicts(self):
        """Test that validation handles lists containing dictionaries."""
        catalog_path = Path("data/soaps.yaml")
        data = {
            "Brand1": {
                "items": [
                    {
                        "name": "Item1",
                        "patterns": ["pattern1"],  # Valid
                    },
                    {
                        "name": "Item2",
                        "patterns": "pattern2",  # Invalid
                    },
                ]
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_patterns_format(data, catalog_path)
        assert "patterns" in str(exc_info.value)
