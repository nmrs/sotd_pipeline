# pylint: disable=redefined-outer-name, protected-access

import pytest
import yaml

from sotd.match.brush_matcher import BrushMatcher


@pytest.fixture(scope="session")
def test_catalog():
    """Create comprehensive test catalog covering all strategy types"""
    return {
        "Simpson": {
            "Chubby 2": {
                "fiber": "Badger",
                "knot_size_mm": 27,
                "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
            },
            "Trafalgar T2": {
                "fiber": "Synthetic",
                "knot_size_mm": 24,
                "patterns": ["simp.*traf.*t2", "trafalgar.*t2"],
            },
        },
        "Declaration Grooming": {
            "fiber": "Badger",
            "knot_size_mm": 28,
            "B3": {"patterns": ["B3(\\.\\s|\\.$|\\s|$)"]},
            "B10": {"patterns": ["b10"]},
            "B15": {"patterns": ["(declaration|\\bdg\\b).*\\bb15\\b", "b15"]},
        },
        "other_brushes": {
            "Elite": {"default": "Badger", "patterns": ["elite"]},
            "Chisel & Hound": {
                "default": "Badger",
                "knot_size_mm": 26,
                "patterns": [
                    "chis.*hou",
                    "chis.*fou",
                    "\\bc(?:\\s*\\&\\s*|\\s+and\\s+|\\s*\\+\\s*)h\\b",
                ],
            },
        },
    }


@pytest.fixture(scope="session")
def test_handles_catalog():
    """Create test handles catalog"""
    return {
        "artisan_handles": {
            "Chisel & Hound": {
                "patterns": [
                    "chis.*hou",
                    "chis.*fou",
                    "\\bc(?:\\s*\\&\\s*|\\s+and\\s+|\\s*\\+\\s*)h\\b",
                ]
            },
        },
        "manufacturer_handles": {"Elite": {"patterns": ["elite"]}},
    }


@pytest.fixture
def brush_matcher(test_catalog, test_handles_catalog, tmp_path):
    """Create brush matcher with test catalogs"""
    # Create temporary catalog files
    catalog_path = tmp_path / "brushes.yaml"
    handles_path = tmp_path / "handles.yaml"
    correct_matches_path = tmp_path / "correct_matches.yaml"

    # Remove 'other_brushes' from the known_brushes dict if present
    known_brushes = dict(test_catalog)
    other_brushes = known_brushes.pop("other_brushes", {})
    catalog_data = {"known_brushes": known_brushes, "other_brushes": other_brushes}

    with catalog_path.open("w", encoding="utf-8") as f:
        yaml.dump(catalog_data, f)

    with handles_path.open("w", encoding="utf-8") as f:
        yaml.dump(test_handles_catalog, f)

    # Create correct matches file with test entries
    correct_matches_data = {
        "handle": {"Chisel & Hound": {"Zebra": ["DG B15 w/ C&H Zebra"]}},
        "knot": {
            "Declaration Grooming": {
                "B15": {"strings": ["DG B15 w/ C&H Zebra"], "fiber": "Badger", "knot_size_mm": 26.0}
            }
        },
    }
    with correct_matches_path.open("w", encoding="utf-8") as f:
        yaml.dump(correct_matches_data, f)

    return BrushMatcher(
        catalog_path=catalog_path,
        handles_path=handles_path,
        correct_matches_path=correct_matches_path,
    )


class TestBrushOutputFormatRefactoring:
    """Test the new brush output format structure."""

    def test_consistent_section_structure_single_brand(self, brush_matcher):
        """Test that single-brand brushes have consistent handle/knot section structure."""
        result = brush_matcher.match("Simpson Chubby 2")

        # REQUIRED: All brushes must have handle and knot sections
        assert "handle" in result.matched
        assert "knot" in result.matched

        # REQUIRED: Handle section must have consistent fields
        handle = result.matched["handle"]
        assert "brand" in handle
        assert "model" in handle
        assert "source_text" in handle
        assert "_matched_by" in handle
        assert "_pattern" in handle

        # REQUIRED: Knot section must have consistent fields
        knot = result.matched["knot"]
        assert "brand" in knot
        assert "model" in knot
        assert "fiber" in knot
        assert "knot_size_mm" in knot
        assert "source_text" in knot
        assert "_matched_by" in knot
        assert "_pattern" in knot

        # VALIDATION: Single-brand brush should have same brand for handle and knot
        assert handle["brand"] == "Simpson"
        assert knot["brand"] == "Simpson"
        assert handle["brand"] == knot["brand"]

    def test_consistent_section_structure_composite_brush(self, brush_matcher):
        """Test that composite brushes have consistent handle/knot section structure."""
        result = brush_matcher.match("DG B15 w/ C&H Zebra")

        # REQUIRED: All brushes must have handle and knot sections
        assert "handle" in result.matched
        assert "knot" in result.matched

        # REQUIRED: Handle section must have consistent fields
        handle = result.matched["handle"]
        assert "brand" in handle
        assert "model" in handle
        assert "source_text" in handle
        assert "_matched_by" in handle
        assert "_pattern" in handle

        # REQUIRED: Knot section must have consistent fields
        knot = result.matched["knot"]
        assert "brand" in knot
        assert "model" in knot
        assert "fiber" in knot
        assert "knot_size_mm" in knot
        assert "source_text" in knot
        assert "_matched_by" in knot
        assert "_pattern" in knot

        # VALIDATION: Composite brush should have different brands for handle and knot
        assert handle["brand"] == "Chisel & Hound"
        assert knot["brand"] == "Declaration Grooming"
        assert handle["brand"] != knot["brand"]

    def test_removed_redundant_fields(self, brush_matcher):
        """Test that redundant fields are removed from single-brand brush output."""
        result = brush_matcher.match("Simpson Chubby 2")

        # VALIDATION: Only expected fields should be present
        expected_fields = {"brand", "model", "handle", "knot"}
        actual_fields = set(result.matched.keys())
        unexpected_fields = actual_fields - expected_fields
        assert not unexpected_fields, f"Unexpected fields found: {unexpected_fields}"

        # VALIDATION: Handle section should only have expected fields
        handle_expected_fields = {"brand", "model", "source_text", "_matched_by", "_pattern"}
        handle_actual_fields = set(result.matched["handle"].keys())
        handle_unexpected_fields = handle_actual_fields - handle_expected_fields
        assert not handle_unexpected_fields, f"Unexpected handle fields: {handle_unexpected_fields}"

        # VALIDATION: Knot section should only have expected fields
        knot_expected_fields = {
            "brand",
            "model",
            "fiber",
            "knot_size_mm",
            "source_text",
            "_matched_by",
            "_pattern",
        }
        knot_actual_fields = set(result.matched["knot"].keys())
        knot_unexpected_fields = knot_actual_fields - knot_expected_fields
        assert not knot_unexpected_fields, f"Unexpected knot fields: {knot_unexpected_fields}"

    def test_removed_redundant_fields_composite(self, brush_matcher):
        """Test that redundant fields are removed from composite brush output."""
        result = brush_matcher.match("DG B15 w/ C&H Zebra")

        # VALIDATION: Only expected fields should be present
        expected_fields = {"brand", "model", "handle", "knot"}
        actual_fields = set(result.matched.keys())
        unexpected_fields = actual_fields - expected_fields
        assert not unexpected_fields, f"Unexpected fields found: {unexpected_fields}"

        # VALIDATION: Handle section should only have expected fields
        handle_expected_fields = {"brand", "model", "source_text", "_matched_by", "_pattern"}
        handle_actual_fields = set(result.matched["handle"].keys())
        handle_unexpected_fields = handle_actual_fields - handle_expected_fields
        assert not handle_unexpected_fields, f"Unexpected handle fields: {handle_unexpected_fields}"

        # VALIDATION: Knot section should only have expected fields
        knot_expected_fields = {
            "brand",
            "model",
            "fiber",
            "knot_size_mm",
            "source_text",
            "_matched_by",
            "_pattern",
        }
        knot_actual_fields = set(result.matched["knot"].keys())
        knot_unexpected_fields = knot_actual_fields - knot_expected_fields
        assert not knot_unexpected_fields, f"Unexpected knot fields: {knot_unexpected_fields}"

    def test_correct_strategy_attribution(self, brush_matcher):
        """Test that handle and knot sections have correct strategy attribution."""
        # Test different scenarios to ensure comprehensive coverage

        # Scenario 1: Correct match (composite brush from correct_matches.yaml)
        result_correct = brush_matcher.match("DG B15 w/ C&H Zebra")
        handle_correct = result_correct.matched["handle"]
        knot_correct = result_correct.matched["knot"]

        # For correct matches, both handle and knot should have CorrectMatches
        assert handle_correct["_matched_by"] == "CorrectMatches", (
            f"Handle should be CorrectMatches for correct match, "
            f"got: {handle_correct['_matched_by']}"
        )
        assert knot_correct["_matched_by"] == "CorrectMatches", (
            f"Knot should be CorrectMatches for correct match, "
            f"got: {knot_correct['_matched_by']}"
        )
        assert handle_correct["_pattern"] == "correct_matches_handle_knot", (
            f"Handle pattern should be correct_matches_handle_knot, "
            f"got: {handle_correct['_pattern']}"
        )
        assert knot_correct["_pattern"] == "correct_matches_handle_knot", (
            f"Knot pattern should be correct_matches_handle_knot, "
            f"got: {knot_correct['_pattern']}"
        )

        # Scenario 2: Strategy-based match (single-brand brush from regex)
        result_strategy = brush_matcher.match("Simpson Chubby 2")
        handle_strategy = result_strategy.matched["handle"]
        knot_strategy = result_strategy.matched["knot"]

        # For strategy-based matches, both handle and knot should have the same strategy
        # (since it's a single-brand brush, both sections come from the same strategy)
        assert handle_strategy["_matched_by"] == knot_strategy["_matched_by"], (
            f"Single-brand brush should have same strategy for handle and knot: "
            f"{handle_strategy['_matched_by']} vs {knot_strategy['_matched_by']}"
        )
        assert handle_strategy["_pattern"] == knot_strategy["_pattern"], (
            f"Single-brand brush should have same pattern for handle and knot: "
            f"{handle_strategy['_pattern']} vs {knot_strategy['_pattern']}"
        )

        # Strategy should be a valid strategy name
        valid_strategies = [
            "KnownBrushMatchingStrategy",
            "CorrectMatches",
            "OtherBrushMatchingStrategy",
            "DeclarationGroomingStrategy",
            "ChiselAndHoundStrategy",
            "ZenithOmegaSemogueStrategy",
        ]
        assert (
            handle_strategy["_matched_by"] in valid_strategies
        ), f"Invalid strategy name: {handle_strategy['_matched_by']}"
        assert (
            knot_strategy["_matched_by"] in valid_strategies
        ), f"Invalid strategy name: {knot_strategy['_matched_by']}"

        # Scenario 3: Test other brush types to ensure consistent attribution
        test_cases = [
            ("Elite handle", "handle-only"),
            ("Declaration B15", "knot-only"),
        ]

        for input_text, brush_type in test_cases:
            result = brush_matcher.match(input_text)
            handle = result.matched["handle"]
            knot = result.matched["knot"]

            # Both sections should have _matched_by and _pattern
            assert "_matched_by" in handle, f"{brush_type} handle should have _matched_by"
            assert "_pattern" in handle, f"{brush_type} handle should have _pattern"
            assert "_matched_by" in knot, f"{brush_type} knot should have _matched_by"
            assert "_pattern" in knot, f"{brush_type} knot should have _pattern"

            # Strategy names should be valid
            assert (
                handle["_matched_by"] in valid_strategies
            ), f"{brush_type} handle has invalid strategy: {handle['_matched_by']}"
            assert (
                knot["_matched_by"] in valid_strategies
            ), f"{brush_type} knot has invalid strategy: {knot['_matched_by']}"

            # Patterns should be non-empty strings
            assert isinstance(
                handle["_pattern"], str
            ), f"{brush_type} handle pattern should be string, got: {type(handle['_pattern'])}"
            assert isinstance(
                knot["_pattern"], str
            ), f"{brush_type} knot pattern should be string, got: {type(knot['_pattern'])}"
            assert len(handle["_pattern"]) > 0, f"{brush_type} handle pattern should not be empty"
            assert len(knot["_pattern"]) > 0, f"{brush_type} knot pattern should not be empty"

        # VALIDATION: No unexpected fields in strategy attribution
        for test_name, result in [("correct", result_correct), ("strategy", result_strategy)]:
            handle = result.matched["handle"]
            knot = result.matched["knot"]

            handle_strategy_fields = {"_matched_by", "_pattern"}
            handle_actual_strategy_fields = set(handle.keys()) & handle_strategy_fields
            handle_unexpected_strategy_fields = (
                handle_actual_strategy_fields - handle_strategy_fields
            )
            assert not handle_unexpected_strategy_fields, (
                f"{test_name} handle has unexpected strategy fields: "
                f"{handle_unexpected_strategy_fields}"
            )

            knot_strategy_fields = {"_matched_by", "_pattern"}
            knot_actual_strategy_fields = set(knot.keys()) & knot_strategy_fields
            knot_unexpected_strategy_fields = knot_actual_strategy_fields - knot_strategy_fields
            assert (
                not knot_unexpected_strategy_fields
            ), f"{test_name} knot has unexpected strategy fields: {knot_unexpected_strategy_fields}"

    def test_simplified_metadata(self, brush_matcher):
        """Test that metadata is simplified and consistent."""
        result = brush_matcher.match("Simpson Chubby 2")

        # VALIDATION: Only simple, consistent metadata should remain
        expected_metadata_fields = {"brand", "model", "handle", "knot"}
        actual_fields = set(result.matched.keys())
        unexpected_metadata_fields = actual_fields - expected_metadata_fields
        assert (
            not unexpected_metadata_fields
        ), f"Unexpected metadata fields: {unexpected_metadata_fields}"

        # VALIDATION: Handle and knot sections should have consistent metadata structure
        handle = result.matched["handle"]
        knot = result.matched["knot"]

        # Both sections should have the same metadata fields
        handle_metadata_fields = {"_matched_by", "_pattern"}
        knot_metadata_fields = {"_matched_by", "_pattern"}

        handle_actual_metadata = set(handle.keys()) & handle_metadata_fields
        knot_actual_metadata = set(knot.keys()) & knot_metadata_fields

        assert (
            handle_actual_metadata == handle_metadata_fields
        ), f"Handle missing metadata fields: {handle_metadata_fields - handle_actual_metadata}"
        assert (
            knot_actual_metadata == knot_metadata_fields
        ), f"Knot missing metadata fields: {knot_metadata_fields - knot_actual_metadata}"

        # VALIDATION: No unexpected metadata fields in sections
        handle_unexpected_metadata = handle_actual_metadata - handle_metadata_fields
        knot_unexpected_metadata = knot_actual_metadata - knot_metadata_fields

        assert (
            not handle_unexpected_metadata
        ), f"Unexpected handle metadata: {handle_unexpected_metadata}"
        assert not knot_unexpected_metadata, f"Unexpected knot metadata: {knot_unexpected_metadata}"

    def test_backward_compatibility_single_brand(self, brush_matcher):
        """Test that single-brand brush functionality is preserved."""
        result = brush_matcher.match("Simpson Chubby 2")

        # REQUIRED: Basic functionality should still work
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"
        assert result.matched["knot"]["fiber"] == "Badger"
        assert result.matched["knot"]["knot_size_mm"] == 27

    def test_backward_compatibility_composite(self, brush_matcher):
        """Test that composite brush functionality is preserved."""
        result = brush_matcher.match("DG B15 w/ C&H Zebra")

        # REQUIRED: Composite brush functionality should still work
        assert result.matched["brand"] is None  # No top-level brand for composites
        assert result.matched["model"] is None  # No top-level model for composites
        assert result.matched["handle"]["brand"] == "Chisel & Hound"
        assert result.matched["knot"]["brand"] == "Declaration Grooming"

    def test_all_brush_types_supported(self, brush_matcher):
        """Test that all brush types work with new format."""
        test_cases = [
            ("Simpson Chubby 2", "single-brand"),
            ("DG B15 w/ C&H Zebra", "composite"),
            ("Elite handle", "handle-only"),
            ("Declaration B15", "knot-only"),
        ]

        for input_text, brush_type in test_cases:
            result = brush_matcher.match(input_text)

            # REQUIRED: All brush types must have handle and knot sections
            assert "handle" in result.matched, f"{brush_type} should have handle section"
            assert "knot" in result.matched, f"{brush_type} should have knot section"

            # REQUIRED: All sections must have required fields
            handle = result.matched["handle"]
            knot = result.matched["knot"]

            assert "brand" in handle, f"{brush_type} handle should have brand"
            assert "source_text" in handle, f"{brush_type} handle should have source_text"
            assert "_matched_by" in handle, f"{brush_type} handle should have _matched_by"
            assert "_pattern" in handle, f"{brush_type} handle should have _pattern"

            assert "brand" in knot, f"{brush_type} knot should have brand"
            assert "source_text" in knot, f"{brush_type} knot should have source_text"
            assert "_matched_by" in knot, f"{brush_type} knot should have _matched_by"
            assert "_pattern" in knot, f"{brush_type} knot should have _pattern"

            # VALIDATION: No unexpected fields in any section
            handle_expected_fields = {"brand", "model", "source_text", "_matched_by", "_pattern"}
            handle_actual_fields = set(handle.keys())
            handle_unexpected_fields = handle_actual_fields - handle_expected_fields
            assert (
                not handle_unexpected_fields
            ), f"{brush_type} handle has unexpected fields: {handle_unexpected_fields}"

            knot_expected_fields = {
                "brand",
                "model",
                "fiber",
                "knot_size_mm",
                "source_text",
                "_matched_by",
                "_pattern",
            }
            knot_actual_fields = set(knot.keys())
            knot_unexpected_fields = knot_actual_fields - knot_expected_fields
            assert (
                not knot_unexpected_fields
            ), f"{brush_type} knot has unexpected fields: {knot_unexpected_fields}"

            # VALIDATION: Top-level should only have expected fields
            top_level_expected_fields = {"brand", "model", "handle", "knot"}
            top_level_actual_fields = set(result.matched.keys())
            top_level_unexpected_fields = top_level_actual_fields - top_level_expected_fields
            assert (
                not top_level_unexpected_fields
            ), f"{brush_type} has unexpected top-level fields: {top_level_unexpected_fields}"

    def test_no_performance_regression(self, brush_matcher):
        """Test that there's no performance regression in brush matching."""
        import time

        test_inputs = [
            "Simpson Chubby 2",
            "DG B15 w/ C&H Zebra",
            "Elite handle",
            "Declaration B15",
        ]

        # Measure performance
        start_time = time.time()
        for _ in range(100):  # Run 100 iterations
            for input_text in test_inputs:
                result = brush_matcher.match(input_text)
                assert result is not None
        end_time = time.time()

        # VALIDATION: Should complete within reasonable time (adjust threshold as needed)
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Performance regression: {execution_time}s for 400 matches"

    def test_data_integrity_preserved(self, brush_matcher):
        """Test that all important data is preserved in new format."""
        result = brush_matcher.match("Simpson Chubby 2")

        # VALIDATION: All important data should be preserved
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"
        assert result.matched["knot"]["fiber"] == "Badger"

        # VALIDATION: No data corruption or unexpected values
        assert result.matched["handle"]["brand"] == "Simpson"
        assert result.matched["handle"]["model"] == "Chubby 2"
        assert result.matched["knot"]["brand"] == "Simpson"
        assert result.matched["knot"]["model"] == "Chubby 2"

        # VALIDATION: No mysterious or corrupted fields
        handle = result.matched["handle"]
        knot = result.matched["knot"]

        # Check for unexpected field types or values
        for field, value in handle.items():
            if field == "brand" and value != "Simpson":
                assert False, f"Handle brand corrupted: {value}"
            if field == "model" and value != "Chubby 2":
                assert False, f"Handle model corrupted: {value}"
            if field == "_matched_by" and value not in [
                "KnownBrushMatchingStrategy",
                "CorrectMatches",
            ]:
                assert False, f"Unexpected handle _matched_by: {value}"
            if field == "_pattern" and value not in [
                "simp.*chubby\\s*2\\b",
                "correct_matches_handle_knot",
            ]:
                assert False, f"Unexpected handle _pattern: {value}"

        for field, value in knot.items():
            if field == "brand" and value != "Simpson":
                assert False, f"Knot brand corrupted: {value}"
            if field == "model" and value != "Chubby 2":
                assert False, f"Knot model corrupted: {value}"
            if field == "fiber" and value != "Badger":
                assert False, f"Knot fiber corrupted: {value}"
            if field == "_matched_by" and value not in [
                "KnownBrushMatchingStrategy",
                "CorrectMatches",
            ]:
                assert False, f"Unexpected knot _matched_by: {value}"
            if field == "_pattern" and value not in [
                "simp.*chubby\\s*2\\b",
                "correct_matches_handle_knot",
            ]:
                assert False, f"Unexpected knot _pattern: {value}"

        # VALIDATION: No mysterious top-level fields
        top_level_fields = set(result.matched.keys())
        expected_top_level_fields = {"brand", "model", "handle", "knot"}
        mysterious_fields = top_level_fields - expected_top_level_fields
        assert not mysterious_fields, f"Mysterious top-level fields found: {mysterious_fields}"

        # VALIDATION: No mysterious section fields
        handle_fields = set(handle.keys())
        expected_handle_fields = {"brand", "model", "source_text", "_matched_by", "_pattern"}
        mysterious_handle_fields = handle_fields - expected_handle_fields
        assert (
            not mysterious_handle_fields
        ), f"Mysterious handle fields found: {mysterious_handle_fields}"

        knot_fields = set(knot.keys())
        expected_knot_fields = {
            "brand",
            "model",
            "fiber",
            "knot_size_mm",
            "source_text",
            "_matched_by",
            "_pattern",
        }
        mysterious_knot_fields = knot_fields - expected_knot_fields
        assert not mysterious_knot_fields, f"Mysterious knot fields found: {mysterious_knot_fields}"

    def test_error_handling_preserved(self, brush_matcher):
        """Test that error handling is preserved with new format."""
        # Test empty input
        result = brush_matcher.match("")
        assert result is None or result.matched is None
        if result is not None:
            assert result.match_type is None

        # Test None input
        result = brush_matcher.match(None)
        assert result is None or result.matched is None
        if result is not None:
            assert result.match_type is None

        # Test unmatched input
        result = brush_matcher.match("Unknown Brush 123")
        assert result is None or result.matched is None
        if result is not None:
            assert result.match_type is None
