#!/usr/bin/env python3
"""Tests for blade pattern extraction utilities."""

from sotd.utils.blade_patterns import (
    extract_blade_count,
    extract_blade_counts,
    extract_escaped_brackets,
    extract_explicit_usage,
    extract_hash_numbers,
    extract_month_usage,
    extract_multipliers,
    extract_ordinal_patterns,
    extract_semantic_patterns,
    extract_simple_delimiters,
    extract_superscript_ordinals,
    validate_usage_count,
)


class TestValidateUsageCount:
    """Test usage count validation logic."""

    def test_valid_ranges(self):
        """Test that valid usage counts are accepted."""
        # Valid ranges
        assert validate_usage_count(1) is True
        assert validate_usage_count(10) is True
        assert validate_usage_count(100) is True
        assert validate_usage_count(799) is True  # Just under 800

    def test_invalid_ranges(self):
        """Test that invalid usage counts are rejected."""
        # Invalid ranges
        assert validate_usage_count(0) is False  # Less than 1
        assert validate_usage_count(-1) is False  # Negative
        assert validate_usage_count(800) is False  # At 800 boundary
        assert validate_usage_count(1000) is False  # 4+ digits
        assert validate_usage_count(3003135) is False  # Model number

    def test_boundary_values(self):
        """Test boundary values for validation."""
        assert validate_usage_count(1) is True  # Lower boundary
        assert validate_usage_count(799) is True  # Upper boundary
        assert validate_usage_count(800) is False  # Upper boundary + 1


class TestExtractSimpleDelimiters:
    """Test extraction of simple delimiter patterns."""

    def test_parentheses_patterns(self):
        """Test extraction from parentheses patterns."""
        assert extract_simple_delimiters("Astra SP (3)") == 3
        assert extract_simple_delimiters("Feather (5)") == 5
        assert extract_simple_delimiters("Gillette (1)") == 1

    def test_bracket_patterns(self):
        """Test extraction from bracket patterns."""
        assert extract_simple_delimiters("Astra SP [4]") == 4
        assert extract_simple_delimiters("Feather [2]") == 2
        assert extract_simple_delimiters("Gillette [10]") == 10

    def test_braces_patterns(self):
        """Test extraction from braces patterns."""
        assert extract_simple_delimiters("Astra SP {7}") == 7
        assert extract_simple_delimiters("Feather {3}") == 3
        assert extract_simple_delimiters("Gillette {15}") == 15

    def test_case_insensitive(self):
        """Test that extraction is case insensitive."""
        assert extract_simple_delimiters("Astra SP (X3)") == 3
        assert extract_simple_delimiters("Feather [X5]") == 5

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_simple_delimiters("Astra SP") is None
        assert extract_simple_delimiters("") is None
        assert extract_simple_delimiters("Just text") is None

    def test_validation_integration(self):
        """Test that validation is integrated with extraction."""
        # High numbers should return None
        assert extract_simple_delimiters("Astra SP (800)") is None
        assert extract_simple_delimiters("Feather [1000]") is None


class TestExtractExplicitUsage:
    """Test extraction of explicit usage patterns."""

    def test_ordinal_with_brackets(self):
        """Test extraction from ordinal patterns with brackets."""
        assert extract_explicit_usage("Astra SP (3rd use)") == 3
        assert extract_explicit_usage("Feather [5th shave]") == 5
        assert extract_explicit_usage("Gillette {2nd use}") == 2

    def test_ordinal_without_brackets(self):
        """Test extraction from ordinal patterns without brackets."""
        assert extract_explicit_usage("Astra SP 3rd use") == 3
        assert extract_explicit_usage("Feather 5th shave") == 5
        assert extract_explicit_usage("Gillette 2nd use") == 2

    def test_case_insensitive(self):
        """Test that extraction is case insensitive."""
        assert extract_explicit_usage("Astra SP (3RD USE)") == 3
        assert extract_explicit_usage("Feather [5TH SHAVE]") == 5

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_explicit_usage("Astra SP") is None
        assert extract_explicit_usage("3rd use") is None  # No brand


class TestExtractMultipliers:
    """Test extraction of multiplier patterns."""

    def test_bracketed_multipliers(self):
        """Test extraction from bracketed multiplier patterns."""
        assert extract_multipliers("Astra SP (2x)") == 2
        assert extract_multipliers("Feather [x3]") == 3
        assert extract_multipliers("Gillette {4x}") == 4

    def test_standalone_multipliers(self):
        """Test extraction from standalone multiplier patterns."""
        assert extract_multipliers("Astra SP x4") == 4
        assert extract_multipliers("Feather 2x") == 2
        assert extract_multipliers("Gillette x5") == 5

    def test_case_insensitive(self):
        """Test that extraction is case insensitive."""
        assert extract_multipliers("Astra SP (2X)") == 2
        assert extract_multipliers("Feather [X3]") == 3

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_multipliers("Astra SP") is None
        assert extract_multipliers("2x") is None  # No brand


class TestExtractHashNumbers:
    """Test extraction of hash number patterns."""

    def test_hash_patterns(self):
        """Test extraction from hash number patterns."""
        assert extract_hash_numbers("Astra SP #15") == 15
        assert extract_hash_numbers("Feather #2") == 2
        assert extract_hash_numbers("Gillette #100") == 100

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_hash_numbers("Astra SP") is None
        assert extract_hash_numbers("#15") is None  # No brand


class TestExtractSemanticPatterns:
    """Test extraction of semantic patterns."""

    def test_bracketed_semantic(self):
        """Test extraction from bracketed semantic patterns."""
        assert extract_semantic_patterns("Astra SP (NEW)") == 1
        assert extract_semantic_patterns("Feather [fresh]") == 1
        assert extract_semantic_patterns("Gillette {new blade}") == 1

    def test_standalone_semantic(self):
        """Test extraction from standalone semantic patterns."""
        assert extract_semantic_patterns("Astra SP new") == 1
        assert extract_semantic_patterns("Feather fresh") == 1
        assert extract_semantic_patterns("Gillette first time") == 1

    def test_case_insensitive(self):
        """Test that extraction is case insensitive."""
        assert extract_semantic_patterns("Astra SP (New)") == 1
        assert extract_semantic_patterns("Feather [Fresh]") == 1

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_semantic_patterns("Astra SP") is None
        assert extract_semantic_patterns("new") is None  # No brand


class TestExtractMonthUsage:
    """Test extraction of month usage patterns."""

    def test_month_patterns(self):
        """Test extraction from month usage patterns."""
        assert extract_month_usage("PolSilver SI 15/31") == 15
        assert extract_month_usage("GSB 20/31") == 20
        assert extract_month_usage("Astra SP 5/30") == 5

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_month_usage("Astra SP") is None
        assert extract_month_usage("15/31") is None  # No brand
        assert extract_month_usage("5/8") is None  # Not month format


class TestExtractOrdinalPatterns:
    """Test extraction of ordinal patterns."""

    def test_ordinal_patterns(self):
        """Test extraction from ordinal patterns."""
        assert extract_ordinal_patterns("Astra SP 3rd") == 3
        assert extract_ordinal_patterns("Feather 2nd") == 2
        assert extract_ordinal_patterns("Gillette 1st") == 1

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_ordinal_patterns("Astra SP") is None
        assert extract_ordinal_patterns("3rd") is None  # No brand


class TestExtractEscapedBrackets:
    """Test extraction of escaped bracket patterns."""

    def test_escaped_patterns(self):
        """Test extraction from escaped bracket patterns."""
        assert extract_escaped_brackets("Astra SP [2\\]") == 2
        assert extract_escaped_brackets("Feather [3\\]") == 3

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_escaped_brackets("Astra SP") is None
        assert extract_escaped_brackets("[2\\]") is None  # No brand


class TestExtractSuperscriptOrdinals:
    """Test extraction of superscript ordinal patterns."""

    def test_superscript_with_use(self):
        """Test extraction from superscript ordinal patterns with 'use'."""
        assert extract_superscript_ordinals("Astra SP (2^(nd) use)") == 2
        assert extract_superscript_ordinals("Feather [3^(rd) use]") == 3

    def test_superscript_without_use(self):
        """Test extraction from superscript ordinal patterns without 'use'."""
        assert extract_superscript_ordinals("Astra SP (2^(nd))") == 2
        assert extract_superscript_ordinals("Feather [3^(rd)]") == 3

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_superscript_ordinals("Astra SP") is None
        assert extract_superscript_ordinals("(2^(nd))") is None  # No brand


class TestExtractBladeCount:
    """Test extraction of blade count patterns."""

    def test_leading_blade_count(self):
        """Test extraction of leading blade count patterns."""
        assert extract_blade_count("[2x] Astra SP") == 2
        assert extract_blade_count("(3x) Feather") == 3
        assert extract_blade_count("{4x} Gillette") == 4

    def test_case_insensitive(self):
        """Test that extraction is case insensitive."""
        assert extract_blade_count("[X2] Astra SP") == 2
        assert extract_blade_count("(x3) Feather") == 3

    def test_no_match(self):
        """Test cases where no pattern is found."""
        assert extract_blade_count("Astra SP") is None
        assert extract_blade_count("Astra SP (2x)") is None  # Not at beginning


class TestExtractBladeCounts:
    """Test the main extraction function with priority logic."""

    def test_priority_logic(self):
        """Test that priority order is respected."""
        # Simple delimiters should win over other patterns
        assert extract_blade_counts("(2x) Astra SP (3)") == (2, 3)
        assert extract_blade_counts("Astra SP (3) #15") == (None, 3)

    def test_multiplier_context(self):
        """Test multiplier context logic."""
        # If both patterns exist: multiplier = blade_count, simple = use_count
        assert extract_blade_counts("(2x) Astra SP (3)") == (2, 3)
        # If only multiplier: multiplier = use_count
        assert extract_blade_counts("Astra SP (3x)") == (None, 3)

    def test_blade_count_stripping(self):
        """Test that blade count is stripped before looking for use count."""
        result = extract_blade_counts("[2x] Astra SP (3)")
        assert result == (2, 3)

    def test_no_blade_count(self):
        """Test extraction when no blade count is present."""
        result = extract_blade_counts("Astra SP (3)")
        assert result == (None, 3)

    def test_validation_integration(self):
        """Test that validation is integrated with extraction."""
        # High numbers should return None
        assert extract_blade_counts("Feather (3003135)") == (None, None)
        # Valid numbers should work normally
        assert extract_blade_counts("Astra SP (3)") == (None, 3)

    def test_real_world_examples(self):
        """Test with real-world comment examples."""
        test_cases = [
            ("Astra SP (3)", (None, 3)),
            ("Feather [5]", (None, 5)),
            ("Gillette Platinum {2}", (None, 2)),
            ("Personna x4", (None, 4)),
            ("Derby (x2)", (None, 2)),
            ("Voskhod 2x", (None, 2)),
            ("(2x) Astra SP (3)", (2, 3)),
            ("[3x] Feather [5]", (3, 5)),
        ]

        for comment, expected in test_cases:
            result = extract_blade_counts(comment)
            assert result == expected, f"Failed for: {comment}"


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        assert extract_blade_counts("") == (None, None)
        # Note: None input is handled by the function's type checking

    def test_whitespace_handling(self):
        """Test handling of various whitespace patterns."""
        assert extract_blade_counts("  Astra SP (3)  ") == (None, 3)
        assert extract_blade_counts("Astra SP  (  3  )") == (None, 3)

    def test_mixed_patterns(self):
        """Test strings with multiple potential patterns."""
        # Should respect priority order
        assert extract_blade_counts("Astra SP (3) [5] {7}") == (None, 3)

    def test_special_characters(self):
        """Test handling of special characters."""
        assert extract_blade_counts("Astra SP (3) #15") == (None, 3)
        assert extract_blade_counts("Feather [5] - great blade!") == (None, 5)
