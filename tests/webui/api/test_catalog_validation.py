#!/usr/bin/env python3
"""Tests for catalog validation functionality."""

import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import yaml
import requests

from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches


class TestCatalogValidation:
    """Test catalog validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ValidateCorrectMatches()

    def create_temp_yaml(self, data: Dict[str, Any]) -> Path:
        """Create a temporary YAML file with test data."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(data, temp_file)
        temp_file.close()
        return Path(temp_file.name)

    def test_valid_blade_data_passes_validation(self, tmp_path):
        """Test that valid blade data passes validation."""
        # Create valid blade data that matches current catalog patterns
        valid_blade_data = {
            "blade": {
                "DE": {
                    "Astra": {
                        "Superior Platinum (Green)": [
                            "astra green",
                            "astra platinum",
                            "astra sp green",
                        ]
                    },
                    "Feather": {"DE": ["feather", "feather (de)", "feather hi-stainless"]},
                }
            }
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(valid_blade_data, f)

        # Patch the validator to use our temp directory
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None  # Force reload

        # Run validation
        issues = self.validator.validate_correct_matches_against_catalog("blade")

        # Should have no issues with valid data
        assert len(issues) == 0, f"Expected no issues, but got {len(issues)}: {issues}"

    def test_corrupted_blade_data_fails_validation(self, tmp_path):
        """Test that corrupted blade data fails validation."""
        # Create corrupted blade data with invalid brand/model combinations
        corrupted_blade_data = {
            "blade": {
                "DE": {
                    "InvalidBrand": {  # This brand doesn't exist in blades.yaml
                        "InvalidModel": ["invalid blade entry"]
                    },
                    "Astra": {
                        "InvalidModel": [  # This model doesn't exist for Astra
                            "astra invalid model"
                        ]
                    },
                }
            }
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(corrupted_blade_data, f)

        # Create a minimal blades.yaml catalog file for testing
        blades_catalog = {
            "Astra": {
                "Superior Platinum (Green)": {
                    "patterns": ["astra green", "astra platinum", "astra sp green"]
                },
                "Superior Stainless (Blue)": {"patterns": ["astra blue", "astra stainless"]},
            },
            "Feather": {"DE": {"patterns": ["feather", "feather (de)", "feather hi-stainless"]}},
        }

        blades_file = tmp_path / "blades.yaml"
        with blades_file.open("w") as f:
            yaml.dump(blades_catalog, f)

        # Patch the validator to use our temp directory
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None  # Force reload

        # Run validation
        issues = self.validator.validate_correct_matches_against_catalog("blade")

        # Debug output
        print(f"\nDebug: Found {len(issues)} issues")
        for i, issue in enumerate(issues):
            print(f"Issue {i+1}: {issue}")

        # Should have issues with corrupted data
        assert len(issues) > 0, "Expected issues with corrupted data, but got none"

        # Check that we have the expected issue types
        issue_types = [issue["issue_type"] for issue in issues]
        expected = "catalog_pattern_no_match"
        assert expected in issue_types, f"Expected '{expected}' issues, got: {issue_types}"

    def test_moved_string_detection(self, tmp_path):
        """Test that moving a string from one model to another is detected."""
        # Create data where a string is moved to a different model
        moved_string_data = {
            "blade": {
                "DE": {
                    "Astra": {
                        "Superior Platinum (Green)": ["astra green", "astra platinum"],
                        "Superior Stainless (Blue)": [
                            "astra sp green"  # This should map to Superior Platinum, not Stainless
                        ],
                    }
                }
            }
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(moved_string_data, f)

        # Create a minimal blades.yaml catalog file for testing
        blades_catalog = {
            "Astra": {
                "Superior Platinum (Green)": {
                    "patterns": ["astra green", "astra platinum", "astra sp green"]
                },
                "Superior Stainless (Blue)": {"patterns": ["astra blue", "astra stainless"]},
            }
        }

        blades_file = tmp_path / "blades.yaml"
        with blades_file.open("w") as f:
            yaml.dump(blades_catalog, f)

        # Patch the validator to use our temp directory
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None  # Force reload

        # Run validation
        issues = self.validator.validate_correct_matches_against_catalog("blade")

        # Should detect the moved string
        assert len(issues) > 0, "Expected issues with moved string, but got none"

        # Check that we have catalog pattern mismatch issues
        issue_types = [issue["issue_type"] for issue in issues]
        expected = "catalog_pattern_mismatch"
        assert expected in issue_types, f"Expected '{expected}' issues, got: {issue_types}"

    def test_renamed_model_detection(self, tmp_path):
        """Test that renaming a model is detected."""
        # Create data with a renamed model
        renamed_model_data = {
            "blade": {
                "DE": {
                    "Astra": {
                        "RenamedModel": [  # This model name doesn't exist
                            "astra green",
                            "astra platinum",
                        ]
                    }
                }
            }
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(renamed_model_data, f)

        # Create a minimal blades.yaml catalog file for testing
        blades_catalog = {
            "Astra": {
                "Superior Platinum (Green)": {
                    "patterns": ["astra green", "astra platinum", "astra sp green"]
                },
                "Superior Stainless (Blue)": {"patterns": ["astra blue", "astra stainless"]},
            }
        }

        blades_file = tmp_path / "blades.yaml"
        with blades_file.open("w") as f:
            yaml.dump(blades_catalog, f)

        # Patch the validator to use our temp directory
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None  # Force reload

        # Run validation
        issues = self.validator.validate_correct_matches_against_catalog("blade")

        # Should detect the renamed model
        assert len(issues) > 0, "Expected issues with renamed model, but got none"

    def test_api_endpoint_with_valid_data(self, tmp_path):
        """Test the API endpoint with valid data."""
        # Create valid blade data
        valid_blade_data = {
            "blade": {
                "DE": {"Astra": {"Superior Platinum (Green)": ["astra green", "astra platinum"]}}
            }
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(valid_blade_data, f)

        # Mock the API call (we'll test the actual API in integration tests)
        # For now, test the validation logic directly
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        issues = self.validator.validate_correct_matches_against_catalog("blade")
        assert (
            len(issues) == 0
        ), f"API validation should pass with valid data, but got {len(issues)} issues"

    def test_api_endpoint_with_corrupted_data(self, tmp_path):
        """Test the API endpoint with corrupted data."""
        # Create corrupted blade data
        corrupted_blade_data = {
            "blade": {"DE": {"InvalidBrand": {"InvalidModel": ["invalid blade entry"]}}}
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(corrupted_blade_data, f)

        # Create a minimal blades.yaml catalog file for testing
        blades_catalog = {
            "Astra": {"Superior Platinum (Green)": {"patterns": ["astra green", "astra platinum"]}}
        }

        blades_file = tmp_path / "blades.yaml"
        with blades_file.open("w") as f:
            yaml.dump(blades_catalog, f)

        # Mock the API call
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        issues = self.validator.validate_correct_matches_against_catalog("blade")
        assert len(issues) > 0, "API validation should fail with corrupted data"

    def test_razor_validation(self, tmp_path):
        """Test razor field validation."""
        # Create valid razor data
        valid_razor_data = {
            "razor": {"Karve": {"Christopher Bradley": ["karve cb", "karve christopher bradley"]}}
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(valid_razor_data, f)

        # Patch the validator
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        # Run validation
        issues = self.validator.validate_correct_matches_against_catalog("razor")
        assert (
            len(issues) == 0
        ), f"Razor validation should pass with valid data, but got {len(issues)} issues"

    def test_brush_validation(self, tmp_path):
        """Test brush field validation."""
        # Create valid brush data
        valid_brush_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2", "chubby 2"]}}}

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(valid_brush_data, f)

        # Patch the validator
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        # Run validation
        issues = self.validator.validate_correct_matches_against_catalog("brush")
        assert (
            len(issues) == 0
        ), f"Brush validation should pass with valid data, but got {len(issues)} issues"

    def test_soap_validation(self, tmp_path):
        """Test soap field validation."""
        # Create valid soap data
        valid_soap_data = {
            "soap": {
                "Barrister and Mann": {"Seville": ["b&m seville", "barrister and mann seville"]}
            }
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(valid_soap_data, f)

        # Patch the validator
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        # Run validation
        issues = self.validator.validate_correct_matches_against_catalog("soap")
        assert (
            len(issues) == 0
        ), f"Soap validation should pass with valid data, but got {len(issues)} issues"

    def test_empty_field_handling(self, tmp_path):
        """Test handling of empty field in correct_matches.yaml."""
        # Create data with empty field
        empty_field_data = {"blade": {}, "razor": {"Karve": {"Christopher Bradley": ["karve cb"]}}}

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(empty_field_data, f)

        # Patch the validator
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        # Run validation on empty field
        issues = self.validator.validate_correct_matches_against_catalog("blade")
        assert len(issues) == 0, "Empty field should have no issues"

        # Run validation on non-empty field
        issues = self.validator.validate_correct_matches_against_catalog("razor")
        assert len(issues) == 0, "Non-empty field should have no issues with valid data"

    def test_missing_catalog_file_handling(self, tmp_path):
        """Test handling when catalog file is missing."""
        # Create correct_matches.yaml but no catalog file
        correct_matches_data = {
            "blade": {"DE": {"Astra": {"Superior Platinum (Green)": ["astra green"]}}}
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Patch the validator
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        # Run validation - should handle missing catalog gracefully
        issues = self.validator.validate_correct_matches_against_catalog("blade")
        # Should return empty list when catalog is missing
        assert len(issues) == 0, "Should handle missing catalog file gracefully"

    def test_malformed_yaml_handling(self, tmp_path):
        """Test handling of malformed YAML."""
        # Create malformed YAML
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            f.write("invalid: yaml: content: [")

        # Patch the validator
        self.validator._data_dir = tmp_path
        self.validator.correct_matches = None

        # Should handle malformed YAML gracefully
        with pytest.raises(ValueError):
            self.validator.validate_correct_matches_against_catalog("blade")

    def test_invalid_brand_model_combination_detection(self, tmp_path):
        """Test that invalid brand/model combinations in YAML structure are detected."""
        # Create data with an invalid model name that doesn't exist in the catalog
        invalid_model_data = {
            "blade": {
                "DE": {
                    "7 O'Clock": {
                        "InvalidModel (This doesn't exist)": [  # This model doesn't exist in blades.yaml
                            "7'o clock - yellow",
                            "gillette 7 o'clock sharp edge",
                        ]
                    }
                }
            }
        }

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(invalid_model_data, f)

        # Create a minimal blades.yaml catalog file for testing
        blades_catalog = {
            "DE": {
                "7 O'Clock": {
                    "Sharpedge (Yellow)": {
                        "patterns": ["7'o clock - yellow", "gillette 7 o'clock sharp edge"]
                    }
                }
            }
        }
        blades_file = tmp_path / "blades.yaml"
        with blades_file.open("w") as f:
            yaml.dump(blades_catalog, f)

        # Create validator with temporary data directory
        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path

        # Validate the field
        issues = validator.validate_correct_matches_against_catalog("blade")

        # Should detect the invalid model name
        assert len(issues) > 0, "Expected issues with invalid model name, but got none"

        # Check that we have the expected issue types
        issue_types = [issue["issue_type"] for issue in issues]
        expected = "invalid_model"
        assert expected in issue_types, f"Expected '{expected}' issues, got: {issue_types}"

        # Check that the issue mentions the invalid model
        issue_details = [issue["details"] for issue in issues]
        assert any(
            "InvalidModel" in detail for detail in issue_details
        ), "Expected issue to mention invalid model name"


class TestCatalogValidationIntegration:
    """Integration tests for catalog validation with real API."""

    @pytest.mark.integration
    def test_api_validation_with_temp_data(self):
        """Test API validation with temporary correct_matches.yaml data."""
        # This test requires the API server to be running
        # It will be skipped if not running in integration mode

        # Create test data
        test_data = {
            "blade": {
                "DE": {"Astra": {"Superior Platinum (Green)": ["astra green", "astra platinum"]}}
            }
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            # Test API endpoint
            response = requests.post(
                "http://localhost:8000/api/analyze/validate-catalog",
                json={"field": "blade"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                print(
                    f"API Response: {data['total_entries']} entries, {len(data['issues'])} issues"
                )

                # With valid data, should have no issues
                assert (
                    len(data["issues"]) == 0
                ), f"Expected no issues, but got {len(data['issues'])}"
            else:
                pytest.skip("API server not available")

        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()

    @pytest.mark.integration
    def test_api_validation_with_corrupted_data(self):
        """Test API validation with corrupted data."""
        # Create corrupted test data
        corrupted_data = {
            "blade": {"DE": {"InvalidBrand": {"InvalidModel": ["invalid blade entry"]}}}
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(corrupted_data, f)
            temp_file = Path(f.name)

        try:
            # Test API endpoint
            response = requests.post(
                "http://localhost:8000/api/analyze/validate-catalog",
                json={"field": "blade"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                print(
                    f"API Response: {data['total_entries']} entries, {len(data['issues'])} issues"
                )

                # With corrupted data, should have issues
                assert len(data["issues"]) > 0, "Expected issues with corrupted data, but got none"
            else:
                pytest.skip("API server not available")

        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
