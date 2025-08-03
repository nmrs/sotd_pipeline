"""Tests for pattern utilities used by brush matching strategies."""

import pytest

from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    compile_catalog_patterns,
    compile_patterns_with_metadata,
    create_default_match_structure,
    create_strategy_result,
    extract_pattern_metadata,
    match_patterns_against_text,
    validate_catalog_structure,
    validate_string_input,
)


class TestValidateStringInput:
    """Test string input validation."""

    def test_valid_string(self):
        """Test that valid strings are normalized."""
        result = validate_string_input("  test string  ")
        assert result == "test string"

    def test_empty_string(self):
        """Test that empty strings are handled."""
        result = validate_string_input("")
        assert result == ""

    def test_whitespace_only(self):
        """Test that whitespace-only strings are handled."""
        result = validate_string_input("   \t\n   ")
        assert result == ""

    def test_non_string_input(self):
        """Test that non-string inputs return None."""
        assert validate_string_input(None) is None
        assert validate_string_input(123) is None
        assert validate_string_input([]) is None
        assert validate_string_input({}) is None


class TestCompilePatternsWithMetadata:
    """Test pattern compilation with metadata."""

    def test_basic_compilation(self):
        """Test basic pattern compilation."""
        patterns_data = [
            {
                "pattern": r"test.*pattern",
                "brand": "TestBrand",
                "model": "TestModel",
            }
        ]

        result = compile_patterns_with_metadata(patterns_data)

        assert len(result) == 1
        assert result[0]["brand"] == "TestBrand"
        assert result[0]["model"] == "TestModel"
        assert result[0]["pattern"] == r"test.*pattern"
        assert hasattr(result[0]["compiled"], "search")

    def test_sorting_by_length(self):
        """Test that patterns are sorted by length (descending)."""
        patterns_data = [
            {"pattern": r"short", "brand": "Short"},
            {"pattern": r"very.*long.*pattern", "brand": "Long"},
            {"pattern": r"medium.*pattern", "brand": "Medium"},
        ]

        result = compile_patterns_with_metadata(patterns_data, sort_by_length=True)

        assert len(result) == 3
        assert result[0]["pattern"] == r"very.*long.*pattern"
        assert result[1]["pattern"] == r"medium.*pattern"
        assert result[2]["pattern"] == r"short"

    def test_no_sorting(self):
        """Test that patterns are not sorted when sort_by_length=False."""
        patterns_data = [
            {"pattern": r"short", "brand": "Short"},
            {"pattern": r"very.*long.*pattern", "brand": "Long"},
        ]

        result = compile_patterns_with_metadata(patterns_data, sort_by_length=False)

        assert len(result) == 2
        assert result[0]["pattern"] == r"short"
        assert result[1]["pattern"] == r"very.*long.*pattern"

    def test_missing_pattern_field(self):
        """Test that entries without pattern field are skipped."""
        patterns_data = [
            {"pattern": r"valid.*pattern", "brand": "Valid"},
            {"brand": "Invalid"},  # Missing pattern
            {"pattern": r"another.*valid", "brand": "AnotherValid"},
        ]

        result = compile_patterns_with_metadata(patterns_data)

        assert len(result) == 2
        assert result[0]["brand"] == "Valid"
        assert result[1]["brand"] == "AnotherValid"

    def test_enhanced_regex_error_reporting(self):
        """Test that malformed regex patterns produce detailed error messages."""
        patterns_data = [
            {
                "pattern": r"invalid[regex",  # Malformed regex - missing closing bracket
                "brand": "TestBrand",
                "model": "TestModel",
            }
        ]
        
        with pytest.raises(ValueError) as exc_info:
            compile_patterns_with_metadata(patterns_data)
        
        error_message = str(exc_info.value)
        assert "Invalid regex pattern" in error_message
        assert "invalid[regex" in error_message
        assert "File: pattern_utils" in error_message
        assert "unterminated character set" in error_message  # The actual regex error


class TestCompileCatalogPatterns:
    """Test catalog pattern compilation."""

    def test_basic_catalog_compilation(self):
        """Test basic catalog pattern compilation."""
        catalog = {
            "Brand1": {
                "Model1": {
                    "patterns": [r"brand1.*model1"],
                    "fiber": "Badger",
                    "knot_size_mm": 28.0,
                }
            },
            "Brand2": {
                "Model2": {
                    "patterns": [r"brand2.*model2"],
                    "fiber": "Boar",
                    "knot_size_mm": 24.0,
                }
            },
        }

        result = compile_catalog_patterns(catalog)

        assert len(result) == 2
        assert result[0]["brand"] == "Brand1"
        assert result[0]["model"] == "Model1"
        assert result[0]["fiber"] == "Badger"
        assert result[0]["knot_size_mm"] == 28.0

    def test_custom_metadata_fields(self):
        """Test compilation with custom metadata fields."""
        catalog = {
            "Brand": {
                "Model": {
                    "patterns": [r"brand.*model"],
                    "custom_field": "custom_value",
                    "another_field": "another_value",
                }
            }
        }

        result = compile_catalog_patterns(
            catalog, metadata_fields=["custom_field", "another_field"]
        )

        assert len(result) == 1
        assert result[0]["custom_field"] == "custom_value"
        assert result[0]["another_field"] == "another_value"

    def test_empty_patterns_skipped(self):
        """Test that entries with empty patterns are skipped."""
        catalog = {
            "Brand1": {
                "Model1": {
                    "patterns": [r"valid.*pattern"],
                    "fiber": "Badger",
                }
            },
            "Brand2": {
                "Model2": {
                    "patterns": [],  # Empty patterns
                    "fiber": "Boar",
                }
            },
            "Brand3": {
                "Model3": {
                    # Missing patterns field
                    "fiber": "Synthetic",
                }
            },
        }

        result = compile_catalog_patterns(catalog)

        assert len(result) == 1
        assert result[0]["brand"] == "Brand1"

    def test_invalid_catalog_structure(self):
        """Test handling of invalid catalog structure."""
        catalog = {
            "Brand1": "not_a_dict",  # Invalid structure
            "Brand2": {
                "Model2": {
                    "patterns": [r"valid.*pattern"],
                    "fiber": "Badger",
                }
            },
        }

        result = compile_catalog_patterns(catalog)

        assert len(result) == 1
        assert result[0]["brand"] == "Brand2"


class TestMatchPatternsAgainstText:
    """Test pattern matching against text."""

    def test_successful_match(self):
        """Test successful pattern matching."""
        patterns = [
            {
                "compiled": compile_patterns_with_metadata(
                    [{"pattern": r"test.*pattern", "brand": "TestBrand"}]
                )[0]["compiled"],
                "brand": "TestBrand",
                "pattern": r"test.*pattern",
            }
        ]

        result = match_patterns_against_text(patterns, "This is a test pattern here")

        assert result is not None
        assert result["brand"] == "TestBrand"
        assert result["pattern"] == r"test.*pattern"

    def test_no_match(self):
        """Test when no patterns match."""
        patterns = [
            {
                "compiled": compile_patterns_with_metadata(
                    [{"pattern": r"nonexistent.*pattern", "brand": "TestBrand"}]
                )[0]["compiled"],
                "brand": "TestBrand",
                "pattern": r"nonexistent.*pattern",
            }
        ]

        result = match_patterns_against_text(patterns, "This text doesn't match")

        assert result is None

    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive."""
        patterns = [
            {
                "compiled": compile_patterns_with_metadata(
                    [{"pattern": r"test.*pattern", "brand": "TestBrand"}]
                )[0]["compiled"],
                "brand": "TestBrand",
                "pattern": r"test.*pattern",
            }
        ]

        result = match_patterns_against_text(patterns, "TEST PATTERN")

        assert result is not None
        assert result["brand"] == "TestBrand"

    def test_first_match_returned(self):
        """Test that first match is returned when return_first_match=True."""
        patterns = [
            {
                "compiled": compile_patterns_with_metadata(
                    [{"pattern": r"first.*pattern", "brand": "FirstBrand"}]
                )[0]["compiled"],
                "brand": "FirstBrand",
                "pattern": r"first.*pattern",
            },
            {
                "compiled": compile_patterns_with_metadata(
                    [{"pattern": r"second.*pattern", "brand": "SecondBrand"}]
                )[0]["compiled"],
                "brand": "SecondBrand",
                "pattern": r"second.*pattern",
            },
        ]

        result = match_patterns_against_text(
            patterns, "first pattern and second pattern", return_first_match=True
        )

        assert result is not None
        assert result["brand"] == "FirstBrand"


class TestCreateDefaultMatchStructure:
    """Test default match structure creation."""

    def test_basic_structure(self):
        """Test basic default match structure."""
        result = create_default_match_structure(
            brand="TestBrand",
            model="TestModel",
            fiber="Badger",
            knot_size_mm=28.0,
        )

        assert result["brand"] == "TestBrand"
        assert result["model"] == "TestModel"
        assert result["fiber"] == "Badger"
        assert result["knot_size_mm"] == 28.0
        assert result["handle_maker"] is None
        assert result["source_text"] is None
        assert result["source_type"] is None

    def test_all_fields(self):
        """Test structure with all fields populated."""
        result = create_default_match_structure(
            brand="TestBrand",
            model="TestModel",
            fiber="Badger",
            knot_size_mm=28.0,
            handle_maker="TestMaker",
            source_text="test source",
            source_type="exact",
        )

        assert result["brand"] == "TestBrand"
        assert result["model"] == "TestModel"
        assert result["fiber"] == "Badger"
        assert result["knot_size_mm"] == 28.0
        assert result["handle_maker"] == "TestMaker"
        assert result["source_text"] == "test source"
        assert result["source_type"] == "exact"


class TestCreateStrategyResult:
    """Test strategy result creation."""

    def test_basic_result(self):
        """Test basic strategy result."""
        matched_data = {"brand": "TestBrand", "model": "TestModel"}

        result = create_strategy_result(
            original_value="test input",
            matched_data=matched_data,
            pattern=r"test.*pattern",
            strategy_name="TestStrategy",
        )

        assert result.original == "test input"
        assert result.matched == matched_data
        assert result.pattern == r"test.*pattern"
        assert result.match_type is None

    def test_with_match_type(self):
        """Test strategy result with match type."""
        result = create_strategy_result(
            original_value="test input",
            matched_data={"brand": "TestBrand"},
            pattern=r"test.*pattern",
            strategy_name="TestStrategy",
            match_type="exact",
        )

        assert result.match_type == "exact"

    def test_no_match_result(self):
        """Test strategy result with no match."""
        result = create_strategy_result(
            original_value="test input",
            matched_data=None,
            pattern=None,
            strategy_name="TestStrategy",
        )

        assert result.original == "test input"
        assert result.matched is None
        assert result.pattern is None


class TestValidateCatalogStructure:
    """Test catalog structure validation."""

    def test_valid_catalog(self):
        """Test validation of valid catalog."""
        catalog = {
            "Brand1": {
                "patterns": [r"pattern1"],
                "default": "Badger",
            },
            "Brand2": {
                "patterns": [r"pattern2"],
                "default": "Boar",
            },
        }

        # Should not raise any exception
        validate_catalog_structure(catalog, ["patterns", "default"])

    def test_invalid_catalog_type(self):
        """Test validation fails for non-dict catalog."""
        with pytest.raises(ValueError, match="catalog must be a dictionary"):
            validate_catalog_structure("not_a_dict", ["patterns"])  # type: ignore

    def test_invalid_brand_structure(self):
        """Test validation fails for invalid brand structure."""
        catalog = {
            "Brand1": "not_a_dict",  # Invalid structure
        }

        with pytest.raises(ValueError, match="Invalid catalog structure for brand"):
            validate_catalog_structure(catalog, ["patterns"])

    def test_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        catalog = {
            "Brand1": {
                "patterns": [r"pattern1"],
                # Missing "default" field
            },
        }

        with pytest.raises(ValueError, match="Missing required fields for brand"):
            validate_catalog_structure(catalog, ["patterns", "default"])

    def test_invalid_patterns_field(self):
        """Test validation fails for invalid patterns field."""
        catalog = {
            "Brand1": {
                "patterns": "not_a_list",  # Should be a list
                "default": "Badger",
            },
        }

        with pytest.raises(ValueError, match="'patterns' field must be a list"):
            validate_catalog_structure(catalog, ["patterns", "default"])


class TestExtractPatternMetadata:
    """Test pattern metadata extraction."""

    def test_basic_extraction(self):
        """Test basic metadata extraction."""
        pattern_entry = {
            "brand": "TestBrand",
            "model": "TestModel",
            "fiber": "Badger",
            "knot_size_mm": 28.0,
            "handle_maker": "TestMaker",
        }

        result = extract_pattern_metadata(pattern_entry, "test source text")

        assert result["brand"] == "TestBrand"
        assert result["model"] == "TestModel"
        assert result["fiber"] == "Badger"
        assert result["knot_size_mm"] == 28.0
        assert result["handle_maker"] == "TestMaker"
        assert result["source_text"] == "test source text"
        assert result["source_type"] == "exact"

    def test_with_defaults(self):
        """Test metadata extraction with defaults."""
        pattern_entry = {
            "brand": "TestBrand",
            "model": "TestModel",
            # Missing fiber and knot_size_mm
        }

        result = extract_pattern_metadata(
            pattern_entry,
            "test source text",
            default_fiber="Synthetic",
            default_knot_size_mm=24.0,
        )

        assert result["brand"] == "TestBrand"
        assert result["model"] == "TestModel"
        assert result["fiber"] == "Synthetic"
        assert result["knot_size_mm"] == 24.0
        assert result["source_text"] == "test source text"
        assert result["source_type"] == "exact"

    def test_removes_none_values(self):
        """Test that None values are removed from result."""
        pattern_entry = {
            "brand": "TestBrand",
            "model": None,
            "fiber": None,
            "knot_size_mm": None,
            "handle_maker": None,
        }

        result = extract_pattern_metadata(pattern_entry, "test source text")

        assert result["brand"] == "TestBrand"
        assert result["source_text"] == "test source text"
        assert result["source_type"] == "exact"
        assert "model" not in result
        assert "fiber" not in result
        assert "knot_size_mm" not in result
        assert "handle_maker" not in result
