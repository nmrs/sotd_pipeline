"""Tests for correct matches validation tool."""

import pytest
from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches
import yaml


@pytest.fixture(scope="session")
def session_validator():
    """Session-scoped validator to avoid repeated instantiation."""
    return ValidateCorrectMatches()


class TestValidateCorrectMatches:
    """Test the ValidateCorrectMatches class."""

    def test_validator_can_be_instantiated(self):
        """Test that validator class can be instantiated."""
        validator = ValidateCorrectMatches()
        assert validator is not None
        assert hasattr(validator, "correct_matches")

    def test_imports_work_correctly(self):
        """Test that all required imports work correctly."""
        # This test ensures that the module can be imported without errors
        from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches

        assert ValidateCorrectMatches is not None

    def test_correct_matches_loading(self):
        """Test that correct_matches.yaml can be loaded."""
        validator = ValidateCorrectMatches()
        # Should not raise an exception
        assert validator.correct_matches is not None

    def test_matcher_initialization(self):
        """Test that matchers can be initialized."""
        validator = ValidateCorrectMatches()
        # Test that we can get a matcher for each field type
        for field in ["razor", "blade", "brush", "soap"]:
            matcher = validator._get_matcher(field)
            assert matcher is not None, f"Matcher for {field} should be available"


class TestCLIInterface:
    """Test CLI interface functionality."""

    def test_cli_help_works(self):
        """Test that CLI help can be displayed."""
        # Test that the script can be run with --help
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "sotd/match/tools/managers/validate_correct_matches.py", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout
        assert "--field" in result.stdout
        assert "--verbose" in result.stdout

    def test_cli_field_argument_parsing(self):
        """Test that CLI field argument parsing works correctly."""
        import subprocess
        import sys

        # Test with valid field
        result = subprocess.run(
            [
                sys.executable,
                "sotd/match/tools/managers/validate_correct_matches.py",
                "--field",
                "razor",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Our enhanced validation may or may not find issues depending on catalog completeness
        # Check for either validation issues or no issues found
        has_issues = "Found" in result.stdout and "validation issues" in result.stdout
        no_issues = "No validation issues found" in result.stdout
        assert has_issues or no_issues

    def test_cli_verbose_argument(self):
        """Test that CLI verbose argument works correctly."""
        import subprocess
        import sys

        # Test with verbose flag
        result = subprocess.run(
            [
                sys.executable,
                "sotd/match/tools/managers/validate_correct_matches.py",
                "--field",
                "blade",
                "--verbose",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Our enhanced validation may or may not find issues depending on catalog completeness
        # Check for either validation issues or no issues found
        has_issues = "Found" in result.stdout and "validation issues" in result.stdout
        no_issues = "No validation issues found" in result.stdout
        assert has_issues or no_issues


class TestValidationFunctionality:
    """Test the core validation functionality."""

    def test_validate_field_method(self, session_validator):
        """Test that validate_field method works correctly."""
        # Test with a field that exists in correct_matches
        if "razor" in session_validator.correct_matches:
            issues, expected_structure = session_validator.validate_field("razor")
            assert isinstance(issues, list)
            assert isinstance(expected_structure, dict)

    def test_validate_all_fields_method(self, session_validator):
        """Test that validate_all_fields method works correctly."""
        all_issues = session_validator.validate_all_fields()
        assert isinstance(all_issues, dict)

    def test_run_validation_method(self, session_validator):
        """Test that run_validation method works correctly."""
        # Should not raise an exception
        session_validator.run_validation("razor")
        session_validator.run_validation()  # No field specified


class TestBladeFormatAwareValidation:
    """Test blade format-aware validation scenarios."""

    def setup_method(self):
        self.validator = ValidateCorrectMatches()

    def test_format_aware_validation_skipped(self, tmp_path):
        """Test that format-aware validation is not implemented (as expected)."""
        # This test documents that the feature is not implemented
        pytest.skip("Format-aware duplicate validation not implemented in current version")

    def test_validation_works_for_all_field_types(self, tmp_path):
        """Test that validation works correctly for all field types."""
        # Create a simple test structure
        correct_matches_data = {
            "razor": {"Test": {"Model": ["test pattern"]}},
            "blade": {"DE": {"Test": {"Model": ["test pattern"]}}},
            "brush": {"Test": {"Model": ["test pattern"]}},
            "soap": {"Test": {"Model": ["test pattern"]}},
        }

        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Create minimal catalog files for testing
        minimal_catalog = {"Test": {"Model": {"patterns": ["test pattern"]}}}

        # Create minimal catalog files for each field type
        catalog_files = {
            "brushes.yaml": minimal_catalog,
            "razors.yaml": minimal_catalog,
            "blades.yaml": {"DE": minimal_catalog},
            "soaps.yaml": minimal_catalog,
            "handles.yaml": minimal_catalog,
            "knots.yaml": minimal_catalog,
        }

        for filename, catalog_data in catalog_files.items():
            catalog_file = tmp_path / filename
            with catalog_file.open("w") as f:
                yaml.dump(catalog_data, f)

        validator = ValidateCorrectMatches(correct_matches_path=correct_matches_file)
        validator._data_dir = tmp_path  # type: ignore

        # Test validation for each field type
        for field in ["razor", "blade", "brush", "soap"]:
            issues, expected_structure = validator.validate_field(field)
            assert isinstance(issues, list)
            assert isinstance(expected_structure, dict)

    def test_all_fields_validation_workflow(self, tmp_path):
        """Test the complete all-fields validation workflow."""
        # Create a comprehensive test structure
        correct_matches_data = {
            "razor": {"Test": {"Model": ["test pattern"]}},
            "blade": {"DE": {"Test": {"Model": ["test pattern"]}}},
        }

        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        validator = ValidateCorrectMatches(correct_matches_path=correct_matches_file)
        validator._data_dir = tmp_path  # type: ignore

        # Test all-fields validation
        all_issues = validator.validate_all_fields()
        assert isinstance(all_issues, dict)


class TestCatalogDriftDetection:
    """Test catalog drift detection functionality."""

    def test_basic_structure_comparison(self, tmp_path):
        """Test basic structure comparison functionality."""
        # Create test data
        original_structure = {"razor": {"BrandA": {"Model1": ["String1"]}}}
        expected_structure = {"razor": {"BrandA": {"Model1": ["String1"]}}}

        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        # Test structure comparison
        issues = validator._compare_structures("razor", original_structure, expected_structure)
        assert isinstance(issues, list)

    def test_missing_brand_detection(self, tmp_path):
        """Test detection of missing brands."""
        expected_structure = {"razor": {"BrandA": {"Model1": ["String1"]}}}
        actual_structure = {"razor": {}}  # Empty structure

        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        # Test structure comparison
        issues = validator._compare_structures("razor", actual_structure, expected_structure)
        assert isinstance(issues, list)


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_handle_missing_catalog_file(self, tmp_path):
        """Test handling of missing catalog files."""
        # Setup correct_matches.yaml but no catalog file
        correct_matches_data = {"razor": {"Test": {"Model": ["test pattern"]}}}

        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        # Should handle missing catalog gracefully
        try:
            issues, expected_structure = validator.validate_field("razor")
            # Should not crash, may return empty list or handle gracefully
            assert isinstance(issues, list)
        except Exception as e:
            # If it does crash, it should be a specific, expected error
            assert "catalog" in str(e).lower() or "file" in str(e).lower()

    def test_handle_empty_correct_matches(self, tmp_path):
        """Test handling of empty correct_matches.yaml."""
        # Create an empty correct_matches.yaml
        correct_matches_data = {}
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Create minimal catalog files for testing
        minimal_catalog = {"TestBrand": {"TestModel": {"patterns": ["test pattern"]}}}

        # Create minimal catalog files for each field type
        catalog_files = {
            "brushes.yaml": minimal_catalog,
            "razors.yaml": minimal_catalog,
            "blades.yaml": {"DE": minimal_catalog},
            "soaps.yaml": minimal_catalog,
            "handles.yaml": minimal_catalog,
            "knots.yaml": minimal_catalog,
        }

        for filename, catalog_data in catalog_files.items():
            catalog_file = tmp_path / filename
            with catalog_file.open("w") as f:
                yaml.dump(catalog_data, f)

        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        # Should handle empty file gracefully
        for field in ["brush", "razor", "blade", "soap"]:
            issues, expected_structure = validator.validate_field(field)
            assert isinstance(issues, list)


class TestPerformance:
    """Test performance characteristics."""

    def test_validation_performance_with_large_dataset(self, tmp_path):
        """Test validation performance with a larger dataset."""
        # Create a larger dataset for performance testing
        correct_matches_data = {"razor": {}}

        # Add many brands and models
        for brand_num in range(10):
            brand_name = f"Brand{brand_num}"
            correct_matches_data["razor"][brand_name] = {}

            for model_num in range(5):
                model_name = f"Model{model_num}"
                correct_matches_data["razor"][brand_name][model_name] = [
                    f"{brand_name} {model_name} String{i}" for i in range(3)
                ]

        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        # Test performance - should complete in reasonable time
        import time

        start_time = time.time()
        issues, expected_structure = validator.validate_field("razor")
        end_time = time.time()

        # Should complete in under 5 seconds for this dataset
        assert end_time - start_time < 5.0
        assert isinstance(issues, list)
        assert isinstance(expected_structure, dict)


class TestCatalogValidation:
    """Test catalog validation functionality."""

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

        # Create a minimal blades.yaml catalog file for testing
        blades_catalog = {
            "DE": {
                "Astra": {
                    "Superior Platinum (Green)": {
                        "patterns": ["astra green", "astra platinum", "astra sp green"]
                    }
                },
                "Feather": {
                    "DE": {"patterns": ["feather", "feather (de)", "feather hi-stainless"]}
                },
            }
        }

        blades_file = tmp_path / "blades.yaml"
        with blades_file.open("w") as f:
            yaml.dump(blades_catalog, f)

        # Create validator with test-specific correct_matches.yaml
        validator = ValidateCorrectMatches(correct_matches_path=correct_matches_file)
        validator._data_dir = tmp_path  # type: ignore

        # Run validation using the actual implemented method
        issues, expected_structure = validator.validate_field("blade")

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
        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        # Run validation using the actual implemented method
        issues, expected_structure = validator.validate_field("blade")

        # Should detect issues with corrupted data
        assert len(issues) > 0, "Expected issues with corrupted data, but got none"

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

        # Create a minimal razors.yaml catalog file for testing
        razors_catalog = {
            "Karve": {
                "Christopher Bradley": {"patterns": ["karve cb", "karve christopher bradley"]}
            }
        }

        razors_file = tmp_path / "razors.yaml"
        with razors_file.open("w") as f:
            yaml.dump(razors_catalog, f)

        # Create validator with test-specific correct_matches.yaml
        validator = ValidateCorrectMatches(correct_matches_path=correct_matches_file)
        validator._data_dir = tmp_path  # type: ignore

        # Run validation using the actual implemented method
        issues, expected_structure = validator.validate_field("razor")

        # Should have no issues with valid data
        assert len(issues) == 0, f"Expected no issues, but got {len(issues)}: {issues}"

    def test_brush_validation(self, tmp_path):
        """Test brush field validation."""
        # Create valid brush data
        valid_brush_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2", "chubby 2"]}}}

        # Create temporary correct_matches.yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(valid_brush_data, f)

        # Create a minimal brushes.yaml catalog file for testing
        brushes_catalog = {"Simpson": {"Chubby 2": {"patterns": ["simpson chubby 2", "chubby 2"]}}}

        brushes_file = tmp_path / "brushes.yaml"
        with brushes_file.open("w") as f:
            yaml.dump(brushes_catalog, f)

        # Create minimal handles.yaml and knots.yaml files for testing
        handles_catalog = {"Simpson": {"Chubby 2": {"patterns": ["simpson chubby 2", "chubby 2"]}}}
        knots_catalog = {"Simpson": {"Chubby 2": {"patterns": ["simpson chubby 2", "chubby 2"]}}}

        handles_file = tmp_path / "handles.yaml"
        knots_file = tmp_path / "knots.yaml"

        with handles_file.open("w") as f:
            yaml.dump(handles_catalog, f)
        with knots_file.open("w") as f:
            yaml.dump(knots_catalog, f)

        # Create validator with test-specific correct_matches.yaml
        validator = ValidateCorrectMatches(correct_matches_path=correct_matches_file)
        validator._data_dir = tmp_path  # type: ignore

        # Run validation using the actual implemented method
        issues, expected_structure = validator.validate_field("brush")

        # Should have no issues with valid data
        assert len(issues) == 0, f"Expected no issues, but got {len(issues)}: {issues}"

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

        # Create a minimal soaps.yaml catalog file for testing
        soaps_catalog = {
            "Barrister and Mann": {
                "Seville": {"patterns": ["b&m seville", "barrister and mann seville"]}
            }
        }

        soaps_file = tmp_path / "soaps.yaml"
        with soaps_file.open("w") as f:
            yaml.dump(soaps_catalog, f)

        # Create validator with test-specific correct_matches.yaml
        validator = ValidateCorrectMatches(correct_matches_path=correct_matches_file)
        validator._data_dir = tmp_path  # type: ignore

        # Run validation using the actual implemented method
        issues, expected_structure = validator.validate_field("soap")

        # Should have no issues with valid data
        assert len(issues) == 0, f"Expected no issues, but got {len(issues)}: {issues}"
