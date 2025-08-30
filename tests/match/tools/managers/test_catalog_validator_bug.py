"""Test to expose the catalog validator bug with brush pattern categorization."""

from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches
from pathlib import Path
import shutil


class TestCatalogValidatorBrushBug:
    """Test to expose the specific bug in brush pattern validation."""

    def test_declaration_grooming_b13_bug(self, tmp_path):
        """Test that exposes the bug where 'declaration grooming - roil jefferson - 28mm b13'
        is incorrectly flagged as needing to be moved to 'Jefferson' section instead of
        'B13' section.

        This pattern should be correctly categorized under B13 (knot model), not Jefferson
        (handle name).
        """

        # Create a minimal correct_matches.yaml with just the problematic entry
        correct_matches_content = """brush:
  Declaration Grooming:
    B13:
      - declaration grooming - roil jefferson - 28mm b13
"""

        correct_matches_file = tmp_path / "correct_matches.yaml"
        correct_matches_file.write_text(correct_matches_content)

        # Create validator with our test file
        validator = ValidateCorrectMatches(correct_matches_path=correct_matches_file)
        validator._data_dir = tmp_path / "data"

        # Instead of creating a minimal brush catalog, copy the real production catalog
        # This ensures the brush matcher has the same working regex patterns
        real_brushes_path = (
            Path(__file__).parent.parent.parent.parent.parent / "data" / "brushes.yaml"
        )
        real_handles_path = (
            Path(__file__).parent.parent.parent.parent.parent / "data" / "handles.yaml"
        )
        real_knots_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "knots.yaml"
        real_scoring_path = (
            Path(__file__).parent.parent.parent.parent.parent / "data" / "brush_scoring_config.yaml"
        )

        # Copy real catalog files to test data directory
        brushes_file = tmp_path / "data" / "brushes.yaml"
        handles_file = tmp_path / "data" / "handles.yaml"
        knots_file = tmp_path / "data" / "knots.yaml"
        scoring_file = tmp_path / "data" / "brush_scoring_config.yaml"

        brushes_file.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(real_brushes_path, brushes_file)
        shutil.copy2(real_handles_path, handles_file)
        shutil.copy2(real_knots_path, knots_file)
        shutil.copy2(real_scoring_path, scoring_file)

        # Copy correct_matches.yaml to the data directory where BrushMatcher expects it
        data_correct_matches = tmp_path / "data" / "correct_matches.yaml"
        data_correct_matches.write_text(correct_matches_content)

        # Now run the validation
        issues, expected_structure = validator.validate_field("brush")

        # Debug output
        print("\n🔍 DEBUG: Validation completed")
        print(f"🔍 DEBUG: Issues found: {len(issues) if issues else 0}")
        if issues:
            for i, issue in enumerate(issues):
                print(f"🔍 DEBUG: Issue {i+1}: {issue}")

        print(f"🔍 DEBUG: Expected structure: {expected_structure}")

        # The bug: This pattern should NOT generate any issues
        # It should be correctly categorized under Declaration Grooming -> B13
        # But the validator is incorrectly suggesting it should be moved to a "Jefferson" section

        # Assert that no issues were found (the pattern is correctly categorized)
        assert not issues, f"Expected no validation issues, but found {len(issues)}: {issues}"

        # When validation passes perfectly (no issues), expected_structure should be empty
        # This indicates that all patterns are correctly categorized
        assert (
            expected_structure == {}
        ), f"Expected empty structure when no issues, but got: {expected_structure}"

        # The pattern should NOT be in any Jefferson section
        # Since there are no issues, we don't need to check the structure
        # The fact that no issues were found means the pattern is correctly categorized

        print("✅ Test passed: Pattern correctly categorized under B13 section")
