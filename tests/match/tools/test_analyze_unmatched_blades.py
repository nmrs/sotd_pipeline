import json
from io import StringIO
import sys
from sotd.match.tools.legacy.analyze_unmatched import main
from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer
from sotd.utils.match_filter_utils import strip_blade_count_patterns


def test_strip_use_count_function():
    """Test the strip_use_count function with various formats."""
    analyzer = UnmatchedAnalyzer()

    # Test that the method returns text as-is since normalization happens in extraction
    assert analyzer._strip_use_count("Feather (3)") == "Feather (3)"
    assert analyzer._strip_use_count("Astra SP [5]") == "Astra SP [5]"
    assert analyzer._strip_use_count("Derby Extra {7}") == "Derby Extra {7}"
    assert analyzer._strip_use_count("Koraat (x2)") == "Koraat (x2)"
    assert analyzer._strip_use_count("Gillette [4x]") == "Gillette [4x]"
    assert analyzer._strip_use_count("Blade (X2)") == "Blade (X2)"
    assert analyzer._strip_use_count("Blade (10)") == "Blade (10)"

    # Test patterns that should NOT be stripped
    assert analyzer._strip_use_count("No Count") == "No Count"
    assert analyzer._strip_use_count("Blade (indian)") == "Blade (indian)"

    # Test that analyzer returns text as-is (normalization happens in extraction)
    test_cases = [
        "Feather (3)",
        "Astra SP [5]",
        "Derby Extra {7}",
        "Koraat (x2)",
        "Gillette [4x]",
        "Blade (X2)",
        "Blade (10)",
        "No Count",
        "Blade (indian)",
    ]

    for test_case in test_cases:
        analyzer_result = analyzer._strip_use_count(test_case)
        # Since normalization happens in extraction, analyzer returns text as-is
        assert analyzer_result == test_case


def test_analyzer_synchronization_with_enrich():
    """Test that analyzer normalization matches enrich phase normalization."""
    analyzer = UnmatchedAnalyzer()

    # Test cases that include the new superscript ordinal patterns
    test_cases = [
        ("Tatra Platinum (2^(nd))", "Tatra Platinum (2^(nd))"),
        ("Feather (3^(rd))", "Feather (3^(rd))"),
        ("Astra (1^(st))", "Astra (1^(st))"),
        ("Derby (4^(th))", "Derby (4^(th))"),
        ("Gillette (2^(nd) use)", "Gillette (2^(nd) use)"),
        ("Personna (3^(rd) use)", "Personna (3^(rd) use)"),
    ]

    for input_text, expected_output in test_cases:
        analyzer_result = analyzer._strip_use_count(input_text)
        shared_result = strip_blade_count_patterns(input_text)

        # Analyzer returns text as-is since normalization happens in extraction
        assert (
            analyzer_result == expected_output
        ), f"Analyzer failed for '{input_text}': got '{analyzer_result}', expected '{expected_output}'"
        # Shared function still does normalization for backward compatibility
        assert (
            shared_result != input_text
        ), f"Shared function should still normalize '{input_text}' but returned '{shared_result}'"
        # Analyzer and shared function should be different since analyzer doesn't normalize
        assert analyzer_result != shared_result, (
            f"Analyzer should not normalize but shared function should: "
            f"analyzer='{analyzer_result}', shared='{shared_result}'"
        )


def test_analyze_unmatched_blades_strips_use_count(tmp_path):
    """Test that analyze_unmatched uses pre-normalized data from extraction."""
    out_dir = tmp_path / "data" / "matched"
    out_dir.mkdir(parents=True)

    file1 = out_dir / "2025-04.json"

    # Create test data with structured format that matches extraction output
    data1 = {
        "data": [
            # Structured blade entries (unmatched) - normalized field already has use counts
            # stripped
            {
                "blade": {
                    "original": "Feather (3)",
                    "normalized": "Feather",
                    "matched": None,
                }
            },
            {
                "blade": {
                    "original": "Feather [5]",
                    "normalized": "Feather",
                    "matched": None,
                }
            },
            {
                "blade": {
                    "original": "Astra SP {2}",
                    "normalized": "Astra SP",
                    "matched": None,
                }
            },
            {
                "blade": {
                    "original": "Astra SP (x4)",
                    "normalized": "Astra SP",
                    "matched": None,
                }
            },
            {
                "blade": {
                    "original": "Derby Extra (7)",
                    "normalized": "Derby Extra",
                    "matched": None,
                }
            },
            {
                "blade": {
                    "original": "Derby Extra [1]",
                    "normalized": "Derby Extra",
                    "matched": None,
                }
            },
            {
                "blade": {
                    "original": "Koraat (2)",
                    "normalized": "Koraat",
                    "matched": None,
                }
            },
            # Matched blade (should be ignored)
            {
                "blade": {
                    "original": "Gillette (3)",
                    "normalized": "Gillette",
                    "matched": {"brand": "Gillette", "model": "DE"},
                }
            },
        ]
    }

    file1.write_text(json.dumps(data1))

    # Capture output
    output = StringIO()
    sys_stdout = sys.stdout
    try:
        sys.stdout = output
        main(["--month", "2025-04", "--out-dir", str(tmp_path / "data"), "--field", "blade"])
    finally:
        sys.stdout = sys_stdout

    result_stdout = output.getvalue()

    # Verify that normalized values (without use counts) are used
    assert "Feather" in result_stdout
    assert "Astra SP" in result_stdout
    assert "Derby Extra" in result_stdout
    assert "Koraat" in result_stdout

    # Verify that use counts are NOT in the output (normalized field is used)
    assert "Feather (3)" not in result_stdout
    assert "Feather [5]" not in result_stdout
    assert "Astra SP {2}" not in result_stdout
    assert "Astra SP (x4)" not in result_stdout
    assert "Derby Extra (7)" not in result_stdout
    assert "Derby Extra [1]" not in result_stdout
    assert "Koraat (2)" not in result_stdout

    # Verify counts are correct (Feather appears twice, Derby Extra twice, others once)
    # Feather and Derby Extra
    assert "(2 uses)" in result_stdout or "2 uses" in result_stdout
    # Astra SP and Koraat
    assert "(1 uses)" in result_stdout or "1 uses" in result_stdout

    # Verify matched blade is not included
    assert "Gillette" not in result_stdout
