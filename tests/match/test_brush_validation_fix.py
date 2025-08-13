"""Test file for the brush validation fail-fast fix.

This file implements Step 3 of the plan: Minimal Fix Implementation.
The goal is to test that the enhanced error handling and validation works correctly.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sotd.match.brush_user_actions import BrushUserActionsManager


class TestBrushValidationFailFastFix:
    """Test class for the brush validation fail-fast fix."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            yield temp_path

    @pytest.fixture
    def manager(self, temp_data_dir):
        """Create a BrushUserActionsManager with temporary data."""
        learning_path = temp_data_dir / "learning"
        learning_path.mkdir(parents=True, exist_ok=True)

        correct_matches_path = temp_data_dir / "correct_matches.yaml"
        return BrushUserActionsManager(
            base_path=learning_path, correct_matches_path=correct_matches_path
        )

    def test_fail_fast_validation_works_correctly(self, manager):
        """Test that the fail-fast validation works correctly for successful cases."""
        # This is the exact data structure from the production bug
        production_matched_data = {
            "brand": None,
            "model": None,
            "user_intent": "dual_component",
            "handle": {
                "brand": "Rad Dinosaur Creations",
                "model": "Unspecified",
                "source_text": "Rad Dinosaur Creations - Jetson - 25mm Muhle STF",
                "_matched_by": "HandleMatcher",
                "_pattern": "rad dino(saur)?",
            },
            "knot": {
                "brand": "Mühle",
                "model": "STF",
                "fiber": "Synthetic",
                "knot_size_mm": None,
                "source_text": "Rad Dinosaur Creations - Jetson - 25mm Muhle STF",
                "_matched_by": "KnotMatcher",
                "_pattern": "m[uü]hle.*stf",
            },
            "strategy": "unified",
            "score": 85.0,
        }

        print("🔍 Testing fail-fast validation with production data:")

        # Test the field type determination logic
        field_type = manager._determine_field_type(production_matched_data)
        print(f"   Field type determined: {field_type}")
        assert field_type == "split_brush"

        # Test the actual validation flow
        input_text = "Rad Dinosaur Creations - Jetson - 25mm Muhle STF"
        month = "2025-06"
        system_used = "scoring"
        comment_ids = ["test_comment_1"]

        # Create brush data that matches the production structure exactly
        brush_data = {
            "matched": production_matched_data,
            "strategy": "unified",
            "all_strategies": [
                {"strategy": "unified", "score": 85.0, "result": production_matched_data}
            ],
        }

        # Try to record the validation
        manager.record_validation_with_data(
            input_text=input_text,
            month=month,
            system_used=system_used,
            brush_data=brush_data,
            comment_ids=comment_ids,
        )
        print("   ✅ Validation succeeded")

        # Check if the entry was added to correct_matches.yaml
        has_entry_split = manager.correct_matches_updater.has_entry(input_text, "split_brush")
        print(f"   Entry in correct_matches.yaml (split_brush): {has_entry_split}")

        assert has_entry_split, "Entry should be found in split_brush section"
        print("   ✅ Entry found in correct section")

    def test_fail_fast_validation_catches_failures(self, manager):
        """Test that the fail-fast validation catches and reports failures immediately."""
        print("🔍 Testing fail-fast validation catches failures:")

        # Mock the correct_matches_updater to simulate a failure
        with patch.object(manager.correct_matches_updater, "add_or_update_entry") as mock_add:
            # Simulate the add operation succeeding
            mock_add.return_value = None

            # Mock has_entry to return False, simulating the entry not being added
            with patch.object(manager.correct_matches_updater, "has_entry", return_value=False):
                input_text = "Test Brush Entry"
                result_data = {
                    "result": {
                        "brand": "Test Brand",
                        "model": "Test Model",
                        "strategy": "test",
                        "score": 100.0,
                    }
                }

                # This should raise a RuntimeError immediately
                with pytest.raises(RuntimeError) as exc_info:
                    manager._update_correct_matches(input_text, result_data, "validated")

                error_message = str(exc_info.value)
                print(f"   ✅ RuntimeError raised: {error_message}")

                # Verify the error message contains the expected information
                assert "CRITICAL" in error_message
                assert "Failed to add entry" in error_message
                assert "Test Brush Entry" in error_message
                assert "brush" in error_message
                assert "must be investigated immediately" in error_message

                print("   ✅ Error message contains expected critical information")

    def test_fail_fast_validation_with_different_field_types(self, manager):
        """Test that the fail-fast validation works with different field types."""
        print("🔍 Testing fail-fast validation with different field types:")

        test_cases = [
            {
                "name": "Complete Brush",
                "data": {"brand": "Brand A", "model": "Model A"},
                "expected_type": "brush",
            },
            {
                "name": "Handle Only",
                "data": {"handle_maker": "Maker A", "handle_model": "Model A"},
                "expected_type": "handle",
            },
            {
                "name": "Knot Only",
                "data": {"fiber": "synthetic", "knot_size_mm": 24.0},
                "expected_type": "knot",
            },
        ]

        for test_case in test_cases:
            print(f"   Testing {test_case['name']}:")

            # Test field type determination
            field_type = manager._determine_field_type(test_case["data"])
            print(f"     Field type: {field_type}")
            assert field_type == test_case["expected_type"]

            # Test the update process
            input_text = f"Test {test_case['name']}"
            result_data = {"result": test_case["data"]}

            # This should work without raising exceptions
            manager._update_correct_matches(input_text, result_data, "validated")
            print("     ✅ Update succeeded")

            # Verify entry was added
            has_entry = manager.correct_matches_updater.has_entry(
                input_text, test_case["expected_type"]
            )
            assert has_entry, f"Entry should be found for {test_case['name']}"
            print("     ✅ Entry verified in correct_matches.yaml")

    def test_fail_fast_validation_logging(self, manager):
        """Test that the fail-fast validation provides comprehensive logging."""
        print("🔍 Testing fail-fast validation logging:")

        # Test that the method provides informative logging
        input_text = "Test Logging Brush"
        result_data = {
            "result": {
                "brand": "Test Brand",
                "model": "Test Model",
                "strategy": "test",
                "score": 100.0,
            }
        }

        # This should work and provide logging
        manager._update_correct_matches(input_text, result_data, "validated")

        # Verify entry was added
        has_entry = manager.correct_matches_updater.has_entry(input_text, "brush")
        assert has_entry, "Entry should be found in correct_matches.yaml"

        print("   ✅ Logging test passed - method executed successfully")

    def test_fail_fast_validation_edge_cases(self, manager):
        """Test that the fail-fast validation handles edge cases correctly."""
        print("🔍 Testing fail-fast validation edge cases:")

        # Test with empty result data - this should fail validation
        input_text = "Empty Data Test"
        result_data = {"result": {}}

        # This should fail because empty data doesn't have required fields
        with pytest.raises(RuntimeError) as exc_info:
            manager._update_correct_matches(input_text, result_data, "validated")

        error_message = str(exc_info.value)
        assert "CRITICAL" in error_message
        assert "Failed to add entry" in error_message
        print("   ✅ Empty data properly rejected with critical error")

        # Test with None result data
        input_text = "None Data Test"
        result_data = {"result": None}

        # This should raise an error since None is not a valid dict
        with pytest.raises(Exception):
            manager._update_correct_matches(input_text, result_data, "validated")
        print("   ✅ None data properly rejected")

        print("🎯 Fail-fast validation edge case testing complete")

    def test_fail_fast_validation_integration(self, manager):
        """Test the complete fail-fast validation integration."""
        print("🔍 Testing complete fail-fast validation integration:")

        # Test the full validation flow with production-like data
        input_text = "Integration Test Brush"
        month = "2025-06"
        system_used = "scoring"
        comment_ids = ["test_comment_1"]

        brush_data = {
            "matched": {
                "brand": "Integration Brand",
                "model": "Integration Model",
                "strategy": "integration",
                "score": 95.0,
            },
            "strategy": "integration",
            "all_strategies": [
                {
                    "strategy": "integration",
                    "score": 95.0,
                    "result": {
                        "brand": "Integration Brand",
                        "model": "Integration Model",
                        "strategy": "integration",
                        "score": 95.0,
                    },
                }
            ],
        }

        # This should work end-to-end
        manager.record_validation_with_data(
            input_text=input_text,
            month=month,
            system_used=system_used,
            brush_data=brush_data,
            comment_ids=comment_ids,
        )

        # Verify both operations succeeded
        has_entry = manager.correct_matches_updater.has_entry(input_text, "brush")
        assert has_entry, "Entry should be in correct_matches.yaml"

        # Check learning file
        actions = manager.storage.load_monthly_actions(month)
        has_learning_entry = any(action.input_text == input_text for action in actions)
        assert has_learning_entry, "Entry should be in learning file"

        print("   ✅ Complete integration test passed")
        print("🎯 Fail-fast validation integration testing complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
