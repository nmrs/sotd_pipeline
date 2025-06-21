"""Tests for validation utilities."""

import pytest

from sotd.utils.validation_utils import (
    validate_boolean_field,
    validate_catalog_structure,
    validate_data_structure,
    validate_field_types,
    validate_list_of_dicts,
    validate_metadata_structure,
    validate_month_format,
    validate_non_empty_strings,
    validate_optional_string_field,
    validate_patterns_field,
    validate_positive_integers,
    validate_range_format,
    validate_records_quality,
    validate_required_fields,
    validate_year_format,
)


class TestValidateListOfDicts:
    """Test validate_list_of_dicts function."""

    def test_valid_list_of_dicts(self):
        """Test with valid list of dictionaries."""
        data = [{"a": 1}, {"b": 2}]
        result = validate_list_of_dicts(data)
        assert result == data

    def test_not_list_raises_error(self):
        """Test that non-list input raises ValueError."""
        with pytest.raises(ValueError, match="data must be a list"):
            validate_list_of_dicts({"a": 1})

    def test_list_with_non_dict_item_raises_error(self):
        """Test that list with non-dict item raises ValueError."""
        with pytest.raises(ValueError, match="data item 1 must be a dictionary"):
            validate_list_of_dicts([{"a": 1}, "not a dict"])

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        with pytest.raises(ValueError, match="custom must be a list"):
            validate_list_of_dicts({"a": 1}, "custom")


class TestValidateRequiredFields:
    """Test validate_required_fields function."""

    def test_all_required_fields_present(self):
        """Test with all required fields present."""
        data = {"a": 1, "b": 2, "c": 3}
        validate_required_fields(data, ["a", "b"])

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raises ValueError."""
        data = {"a": 1, "c": 3}
        with pytest.raises(ValueError, match="data missing required fields: \\['b'\\]"):
            validate_required_fields(data, ["a", "b", "c"])

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        data = {"a": 1}
        with pytest.raises(ValueError, match="custom missing required fields: \\['b'\\]"):
            validate_required_fields(data, ["a", "b"], "custom")


class TestValidateFieldTypes:
    """Test validate_field_types function."""

    def test_all_fields_have_correct_types(self):
        """Test with all fields having correct types."""
        data = {"a": 1, "b": "string", "c": True}
        field_types = {"a": int, "b": str, "c": bool}
        validate_field_types(data, field_types)

    def test_field_with_incorrect_type_raises_error(self):
        """Test that field with incorrect type raises ValueError."""
        data = {"a": "string", "b": 123}
        field_types = {"a": int, "b": str}
        with pytest.raises(ValueError, match="data field 'a' must be int, got str"):
            validate_field_types(data, field_types)

    def test_missing_field_ignored(self):
        """Test that missing fields are ignored."""
        data = {"a": 1}
        field_types = {"a": int, "b": str}
        validate_field_types(data, field_types)

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        data = {"a": "string"}
        field_types = {"a": int}
        with pytest.raises(ValueError, match="custom field 'a' must be int, got str"):
            validate_field_types(data, field_types, "custom")


class TestValidateNonEmptyStrings:
    """Test validate_non_empty_strings function."""

    def test_all_string_fields_non_empty(self):
        """Test with all string fields being non-empty."""
        data = {"a": "hello", "b": "world"}
        validate_non_empty_strings(data, ["a", "b"])

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        data = {"a": "hello", "b": ""}
        with pytest.raises(ValueError, match="data field 'b' must be a non-empty string"):
            validate_non_empty_strings(data, ["a", "b"])

    def test_whitespace_only_string_raises_error(self):
        """Test that whitespace-only string raises ValueError."""
        data = {"a": "hello", "b": "   "}
        with pytest.raises(ValueError, match="data field 'b' must be a non-empty string"):
            validate_non_empty_strings(data, ["a", "b"])

    def test_non_string_field_raises_error(self):
        """Test that non-string field raises ValueError."""
        data = {"a": "hello", "b": 123}
        with pytest.raises(ValueError, match="data field 'b' must be a non-empty string"):
            validate_non_empty_strings(data, ["a", "b"])

    def test_missing_field_ignored(self):
        """Test that missing fields are ignored."""
        data = {"a": "hello"}
        validate_non_empty_strings(data, ["a", "b"])

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        data = {"a": ""}
        with pytest.raises(ValueError, match="custom field 'a' must be a non-empty string"):
            validate_non_empty_strings(data, ["a"], "custom")


class TestValidatePositiveIntegers:
    """Test validate_positive_integers function."""

    def test_all_integer_fields_positive(self):
        """Test with all integer fields being positive."""
        data = {"a": 1, "b": 100, "c": 1.5}
        validate_positive_integers(data, ["a", "b", "c"])

    def test_zero_raises_error(self):
        """Test that zero raises ValueError."""
        data = {"a": 1, "b": 0}
        with pytest.raises(ValueError, match="data field 'b' must be a positive number"):
            validate_positive_integers(data, ["a", "b"])

    def test_negative_number_raises_error(self):
        """Test that negative number raises ValueError."""
        data = {"a": 1, "b": -5}
        with pytest.raises(ValueError, match="data field 'b' must be a positive number"):
            validate_positive_integers(data, ["a", "b"])

    def test_non_numeric_field_raises_error(self):
        """Test that non-numeric field raises ValueError."""
        data = {"a": 1, "b": "string"}
        with pytest.raises(ValueError, match="data field 'b' must be a positive number"):
            validate_positive_integers(data, ["a", "b"])

    def test_missing_field_ignored(self):
        """Test that missing fields are ignored."""
        data = {"a": 1}
        validate_positive_integers(data, ["a", "b"])

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        data = {"a": -1}
        with pytest.raises(ValueError, match="custom field 'a' must be a positive number"):
            validate_positive_integers(data, ["a"], "custom")


class TestValidateDataStructure:
    """Test validate_data_structure function."""

    def test_all_required_sections_present(self):
        """Test with all required sections present."""
        data = {"meta": {}, "data": {}, "extra": {}}
        validate_data_structure(data, ["meta", "data"])

    def test_missing_section_raises_error(self):
        """Test that missing section raises ValueError."""
        data = {"meta": {}}
        with pytest.raises(ValueError, match="data missing required sections: \\['data'\\]"):
            validate_data_structure(data, ["meta", "data"])

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        data = {"meta": {}}
        with pytest.raises(ValueError, match="custom missing required sections: \\['data'\\]"):
            validate_data_structure(data, ["meta", "data"], "custom")


class TestValidateMetadataStructure:
    """Test validate_metadata_structure function."""

    def test_valid_metadata(self):
        """Test with valid metadata."""
        metadata = {"total_shaves": 100, "unique_shavers": 50}
        validate_metadata_structure(metadata)

    def test_not_dict_raises_error(self):
        """Test that non-dict input raises ValueError."""
        with pytest.raises(ValueError, match="Metadata must be a dictionary"):
            validate_metadata_structure([])  # type: ignore

    def test_missing_standard_fields_raises_error(self):
        """Test that missing standard fields raises ValueError."""
        metadata = {"total_shaves": 100}
        with pytest.raises(
            ValueError, match="metadata missing required fields: \\['unique_shavers'\\]"
        ):
            validate_metadata_structure(metadata)

    def test_wrong_field_types_raises_error(self):
        """Test that wrong field types raises ValueError."""
        metadata = {"total_shaves": "100", "unique_shavers": 50}
        with pytest.raises(ValueError, match="metadata field 'total_shaves' must be int, got str"):
            validate_metadata_structure(metadata)

    def test_non_positive_integers_raises_error(self):
        """Test that non-positive integers raises ValueError."""
        metadata = {"total_shaves": 0, "unique_shavers": 50}
        with pytest.raises(
            ValueError, match="metadata field 'total_shaves' must be a positive number"
        ):
            validate_metadata_structure(metadata)

    def test_with_additional_required_fields(self):
        """Test with additional required fields."""
        metadata = {"total_shaves": 100, "unique_shavers": 50, "custom": "value"}
        validate_metadata_structure(metadata, ["custom"])

    def test_missing_additional_fields_raises_error(self):
        """Test that missing additional fields raises ValueError."""
        metadata = {"total_shaves": 100, "unique_shavers": 50}
        with pytest.raises(ValueError, match="metadata missing required fields: \\['custom'\\]"):
            validate_metadata_structure(metadata, ["custom"])


class TestValidateRecordsQuality:
    """Test validate_records_quality function."""

    def test_valid_records(self):
        """Test with valid records."""
        records = [{"author": "user1"}, {"author": "user2"}]
        validate_records_quality(records)

    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="No records to process"):
            validate_records_quality([])

    def test_no_valid_authors_raises_error(self):
        """Test that no valid authors raises ValueError."""
        records = [{"author": ""}, {"author": "   "}, {"other": "field"}]
        with pytest.raises(ValueError, match="No valid authors found in records"):
            validate_records_quality(records)

    def test_records_with_valid_authors(self):
        """Test with records containing valid authors."""
        records = [{"author": "user1"}, {"author": "user2"}, {"author": ""}]
        validate_records_quality(records)  # Should not raise error


class TestValidateCatalogStructure:
    """Test validate_catalog_structure function."""

    def test_valid_catalog(self):
        """Test with valid catalog."""
        catalog = {
            "brand1": {"patterns": ["pattern1"], "default": "badger"},
            "brand2": {"patterns": ["pattern2"], "default": "synthetic"},
        }
        validate_catalog_structure(catalog, ["patterns", "default"])

    def test_not_dict_raises_error(self):
        """Test that non-dict input raises ValueError."""
        with pytest.raises(ValueError, match="catalog must be a dictionary"):
            validate_catalog_structure([], ["patterns"])  # type: ignore

    def test_brand_not_dict_raises_error(self):
        """Test that brand entry not being dict raises ValueError."""
        catalog = {"brand1": "not a dict"}
        with pytest.raises(
            ValueError, match="Invalid catalog structure for brand 'brand1': must be a dictionary"
        ):
            validate_catalog_structure(catalog, ["patterns"])

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raises ValueError."""
        catalog = {"brand1": {"patterns": ["pattern1"]}}
        with pytest.raises(
            ValueError,
            match="Missing required fields for brand 'brand1' in catalog: \\['default'\\]",
        ):
            validate_catalog_structure(catalog, ["patterns", "default"])

    def test_custom_catalog_name(self):
        """Test with custom catalog name in error message."""
        catalog = {"brand1": "not a dict"}
        with pytest.raises(
            ValueError, match="Invalid custom structure for brand 'brand1': must be a dictionary"
        ):
            validate_catalog_structure(catalog, ["patterns"], "custom")


class TestValidatePatternsField:
    """Test validate_patterns_field function."""

    def test_valid_patterns(self):
        """Test with valid patterns."""
        patterns = ["pattern1", "pattern2"]
        validate_patterns_field(patterns, "brand1")

    def test_not_list_raises_error(self):
        """Test that non-list input raises ValueError."""
        with pytest.raises(
            ValueError, match="'patterns' field must be a list for brand 'brand1' in catalog"
        ):
            validate_patterns_field("not a list", "brand1")

    def test_pattern_not_string_raises_error(self):
        """Test that pattern not being string raises ValueError."""
        with pytest.raises(
            ValueError, match="Pattern 1 for brand 'brand1' must be a string in catalog"
        ):
            validate_patterns_field(["pattern1", 123], "brand1")

    def test_custom_catalog_name(self):
        """Test with custom catalog name in error message."""
        with pytest.raises(
            ValueError, match="'patterns' field must be a list for brand 'brand1' in custom"
        ):
            validate_patterns_field("not a list", "brand1", "custom")


class TestValidateMonthFormat:
    """Test validate_month_format function."""

    def test_valid_month(self):
        """Test with valid month format."""
        assert validate_month_format("2024-01") == "2024-01"
        assert validate_month_format("2024-12") == "2024-12"

    def test_not_string_raises_error(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Month must be a string"):
            validate_month_format(2024)  # type: ignore

    def test_wrong_format_raises_error(self):
        """Test that wrong format raises ValueError."""
        with pytest.raises(ValueError, match="Month must be in YYYY-MM format"):
            validate_month_format("2024/01")

    def test_invalid_year_raises_error(self):
        """Test that invalid year raises ValueError."""
        with pytest.raises(ValueError, match="Year must be between 1900 and 2100"):
            validate_month_format("1800-01")

    def test_invalid_month_raises_error(self):
        """Test that invalid month raises ValueError."""
        with pytest.raises(ValueError, match="Month must be between 01 and 12"):
            validate_month_format("2024-13")

    def test_non_numeric_raises_error(self):
        """Test that non-numeric input raises ValueError."""
        with pytest.raises(ValueError, match="Month must be in YYYY-MM format with valid numbers"):
            validate_month_format("abcd-ef")


class TestValidateYearFormat:
    """Test validate_year_format function."""

    def test_valid_year(self):
        """Test with valid year format."""
        assert validate_year_format("2024") == "2024"
        assert validate_year_format("1990") == "1990"

    def test_not_string_raises_error(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Year must be a string"):
            validate_year_format(2024)  # type: ignore

    def test_wrong_format_raises_error(self):
        """Test that wrong format raises ValueError."""
        with pytest.raises(ValueError, match="Year must be in YYYY format"):
            validate_year_format("24")

    def test_invalid_year_raises_error(self):
        """Test that invalid year raises ValueError."""
        with pytest.raises(ValueError, match="Year must be between 1900 and 2100"):
            validate_year_format("1800")

    def test_non_numeric_raises_error(self):
        """Test that non-numeric input raises ValueError."""
        with pytest.raises(ValueError, match="Year must be in YYYY format with valid numbers"):
            validate_year_format("abcd")


class TestValidateRangeFormat:
    """Test validate_range_format function."""

    def test_valid_range(self):
        """Test with valid range format."""
        assert validate_range_format("2024-01:2024-12") == "2024-01:2024-12"

    def test_not_string_raises_error(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Date range must be a string"):
            validate_range_format(2024)  # type: ignore

    def test_wrong_format_raises_error(self):
        """Test that wrong format raises ValueError."""
        with pytest.raises(ValueError, match="Date range must be in YYYY-MM:YYYY-MM format"):
            validate_range_format("2024-01")

    def test_start_after_end_raises_error(self):
        """Test that start after end raises ValueError."""
        with pytest.raises(ValueError, match="Start month must be before end month"):
            validate_range_format("2024-12:2024-01")

    def test_same_start_end_raises_error(self):
        """Test that same start and end raises ValueError."""
        with pytest.raises(ValueError, match="Start month must be before end month"):
            validate_range_format("2024-01:2024-01")


class TestValidateBooleanField:
    """Test validate_boolean_field function."""

    def test_valid_boolean(self):
        """Test with valid boolean values."""
        assert validate_boolean_field(True, "field") is True
        assert validate_boolean_field(False, "field") is False

    def test_not_boolean_raises_error(self):
        """Test that non-boolean input raises ValueError."""
        with pytest.raises(ValueError, match="data field 'field' must be a boolean"):
            validate_boolean_field("true", "field")

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        with pytest.raises(ValueError, match="custom field 'field' must be a boolean"):
            validate_boolean_field("true", "field", "custom")


class TestValidateOptionalStringField:
    """Test validate_optional_string_field function."""

    def test_none_value(self):
        """Test with None value."""
        assert validate_optional_string_field(None, "field") is None

    def test_valid_string(self):
        """Test with valid string."""
        assert validate_optional_string_field("hello", "field") == "hello"

    def test_empty_string_returns_none(self):
        """Test that empty string returns None."""
        assert validate_optional_string_field("", "field") is None

    def test_whitespace_string_returns_none(self):
        """Test that whitespace-only string returns None."""
        assert validate_optional_string_field("   ", "field") is None

    def test_stripped_string(self):
        """Test that string is stripped."""
        assert validate_optional_string_field("  hello  ", "field") == "hello"

    def test_not_string_raises_error(self):
        """Test that non-string input raises ValueError."""
        with pytest.raises(ValueError, match="data field 'field' must be None or a string"):
            validate_optional_string_field(123, "field")

    def test_custom_data_name(self):
        """Test with custom data name in error message."""
        with pytest.raises(ValueError, match="custom field 'field' must be None or a string"):
            validate_optional_string_field(123, "field", "custom")
