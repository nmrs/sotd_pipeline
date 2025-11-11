"""
Tests for data structure validation functionality.

This module tests the data structure validation rules for correct_matches.yaml.
"""

from pathlib import Path

from sotd.validate.actual_matching_validator import ActualMatchingValidator


class TestDataStructureValidation:
    """Test cases for data structure validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ActualMatchingValidator(data_path=Path("data"))

    def test_validate_data_structure_empty_data(self):
        """Test data structure validation with empty data."""
        correct_matches = {}
        issues = self.validator._validate_data_structure(correct_matches)
        assert len(issues) == 0

    def test_validate_data_structure_invalid_structure(self):
        """Test data structure validation with invalid structure."""
        correct_matches = {"brush": "not_a_dict"}  # Invalid structure
        issues = self.validator._validate_data_structure(correct_matches)
        assert len(issues) == 0  # Should skip invalid structures gracefully

    def test_validate_data_structure_duplicate_strings_same_brand_model(self):
        """Test duplicate strings within same brand/model."""
        correct_matches = {
            "brush": {
                "AP Shave Co": {
                    "Mixed Badger/Boar": [
                        "ap shaveco 24mm luxury mixed knot",
                        "ap shaveco 24mm luxury mixed knot",  # Duplicate
                    ]
                }
            }
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == "duplicate_string"
        assert issue.severity == "low"
        assert issue.correct_match == "ap shaveco 24mm luxury mixed knot"
        assert "Duplicate string" in issue.details
        assert "brush section" in issue.details

    def test_validate_data_structure_duplicate_strings_different_brands(self):
        """Test duplicate strings across different brands."""
        correct_matches = {
            "brush": {
                "AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]},
                "Different Brand": {
                    "Different Model": ["ap shaveco 24mm luxury mixed knot"]  # Duplicate
                },
            }
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == "duplicate_string"
        assert issue.severity == "low"
        assert issue.correct_match == "ap shaveco 24mm luxury mixed knot"

    def test_validate_data_structure_duplicate_strings_different_models(self):
        """Test duplicate strings across different models."""
        correct_matches = {
            "brush": {
                "AP Shave Co": {
                    "Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"],
                    "Different Model": ["ap shaveco 24mm luxury mixed knot"],  # Duplicate
                }
            }
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == "duplicate_string"
        assert issue.severity == "low"
        assert issue.correct_match == "ap shaveco 24mm luxury mixed knot"

    def test_validate_data_structure_duplicate_strings_multiple_sections(self):
        """Test duplicate strings across multiple sections."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "razor": {
                "Different Brand": {
                    "Different Model": ["ap shaveco 24mm luxury mixed knot"]  # Duplicate
                }
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == "duplicate_string"
        assert issue.severity == "low"
        assert issue.correct_match == "ap shaveco 24mm luxury mixed knot"

    def test_validate_data_structure_cross_section_conflict_brush_and_handle(self):
        """Test cross-section conflict between brush and handle sections."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "handle": {
                "AP Shave Co": {"Unspecified": ["ap shaveco 24mm luxury mixed knot"]}  # Conflict
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == "cross_section_conflict"
        assert issue.severity == "high"
        assert issue.correct_match == "ap shaveco 24mm luxury mixed knot"
        assert "appears in both brush and handle sections" in issue.details

    def test_validate_data_structure_cross_section_conflict_brush_and_knot(self):
        """Test cross-section conflict between brush and knot sections."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "knot": {
                "AP Shave Co": {
                    "Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]  # Conflict
                }
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == "cross_section_conflict"
        assert issue.severity == "high"
        assert issue.correct_match == "ap shaveco 24mm luxury mixed knot"

    def test_validate_data_structure_cross_section_conflict_brush_and_handle_and_knot(self):
        """Test cross-section conflict between brush, handle, and knot sections."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "handle": {
                "AP Shave Co": {"Unspecified": ["ap shaveco 24mm luxury mixed knot"]}  # Conflict
            },
            "knot": {
                "AP Shave Co": {
                    "Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]  # Conflict
                }
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        # Should find 3 conflicts: brush-handle, brush-knot, and handle-knot
        assert len(issues) == 3
        issue = issues[0]
        assert issue.issue_type == "cross_section_conflict"
        assert issue.severity == "high"
        assert issue.correct_match == "ap shaveco 24mm luxury mixed knot"

    def test_validate_data_structure_cross_section_conflict_handle_and_knot(self):
        """Test cross-section conflict between handle and knot sections (valid)."""
        correct_matches = {
            "handle": {
                "Chisel & Hound": {
                    "Tahitian Pearl": ["chisel & hound tahitian pearl 26mm maggard shd"]
                }
            },
            "knot": {
                "Maggard": {
                    "SHD": [
                        "chisel & hound tahitian pearl 26mm maggard shd"
                    ]  # Same string, different sections
                }
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        # This should be valid - handle and knot can share the same string
        assert len(issues) == 0

    def test_validate_data_structure_no_conflicts_valid_structure(self):
        """Test data structure validation with valid structure and no conflicts."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "handle": {
                "Chisel & Hound": {
                    "Tahitian Pearl": ["chisel & hound tahitian pearl 26mm maggard shd"]
                }
            },
            "knot": {"Maggard": {"SHD": ["chisel & hound tahitian pearl 26mm maggard shd"]}},
            "razor": {"Koraat": {"Moarteen": ["koraat moarteen"]}},
        }

        issues = self.validator._validate_data_structure(correct_matches)
        assert len(issues) == 0

    def test_validate_data_structure_multiple_duplicates(self):
        """Test data structure validation with multiple duplicate strings."""
        correct_matches = {
            "brush": {
                "AP Shave Co": {
                    "Mixed Badger/Boar": [
                        "ap shaveco 24mm luxury mixed knot",
                        "ap shaveco 24mm luxury mixed knot",  # Duplicate 1
                        "different string",
                    ]
                }
            },
            "razor": {
                "Koraat": {"Moarteen": ["koraat moarteen", "koraat moarteen"]}  # Duplicate 2
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 2
        duplicate_issues = [i for i in issues if i.issue_type == "duplicate_string"]
        assert len(duplicate_issues) == 2

        # Check that both duplicates are detected
        duplicate_strings = [i.correct_match for i in duplicate_issues]
        assert "ap shaveco 24mm luxury mixed knot" in duplicate_strings
        assert "koraat moarteen" in duplicate_strings

    def test_validate_data_structure_mixed_issues(self):
        """Test data structure validation with both duplicates and conflicts."""
        correct_matches = {
            "brush": {
                "AP Shave Co": {
                    "Mixed Badger/Boar": [
                        "ap shaveco 24mm luxury mixed knot",
                        "ap shaveco 24mm luxury mixed knot",  # Duplicate
                    ]
                }
            },
            "handle": {
                "AP Shave Co": {"Unspecified": ["ap shaveco 24mm luxury mixed knot"]}  # Conflict
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 2

        # Check for duplicate issue
        duplicate_issues = [i for i in issues if i.issue_type == "duplicate_string"]
        assert len(duplicate_issues) == 1
        assert duplicate_issues[0].correct_match == "ap shaveco 24mm luxury mixed knot"

        # Check for conflict issue
        conflict_issues = [i for i in issues if i.issue_type == "cross_section_conflict"]
        assert len(conflict_issues) == 1
        assert conflict_issues[0].correct_match == "ap shaveco 24mm luxury mixed knot"

    def test_validate_data_structure_invalid_nested_structure(self):
        """Test data structure validation with invalid nested structures."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": "not_a_list"}},  # Invalid structure
            "razor": {"Koraat": "not_a_dict"},  # Invalid structure
        }

        issues = self.validator._validate_data_structure(correct_matches)

        # Should handle invalid structures gracefully and not crash
        assert len(issues) == 0

    def test_validate_data_structure_empty_sections(self):
        """Test data structure validation with empty sections."""
        correct_matches = {
            "brush": {},
            "razor": {"Koraat": {}},
            "blade": {"Feather": {"ProGuard": []}},
        }

        issues = self.validator._validate_data_structure(correct_matches)
        assert len(issues) == 0

    def test_validate_data_structure_none_values(self):
        """Test data structure validation with None values."""
        correct_matches = {"brush": None, "razor": {"Koraat": None}}

        issues = self.validator._validate_data_structure(correct_matches)

        # Should handle None values gracefully
        assert len(issues) == 0
