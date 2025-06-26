import json
from io import StringIO
import sys
from sotd.match.tools.legacy.analyze_unmatched import main
from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer


def test_strip_use_count_function():
    """Test the strip_use_count function with various formats."""
    analyzer = UnmatchedAnalyzer()
    assert analyzer._strip_use_count("Feather (3)") == "Feather"
    assert analyzer._strip_use_count("Astra SP [5]") == "Astra SP"
    assert analyzer._strip_use_count("Derby Extra {7}") == "Derby Extra"
    assert analyzer._strip_use_count("Koraat (x2)") == "Koraat"
    assert analyzer._strip_use_count("Gillette [4x]") == "Gillette"
    assert analyzer._strip_use_count("Blade (X2)") == "Blade"
    assert analyzer._strip_use_count("No Count") == "No Count"
    assert analyzer._strip_use_count("Blade (10)") == "Blade"


def test_analyze_unmatched_blades_strips_use_count(tmp_path):
    """Test that analyze_unmatched strips use counts from blade entries."""
    out_dir = tmp_path / "data" / "matched"
    out_dir.mkdir(parents=True)

    file1 = out_dir / "2025-04.json"

    # Create test data with blade entries that have use counts
    data1 = {
        "data": [
            # String blade entries (unmatched)
            {"blade": "Feather (3)"},
            {"blade": "Feather [5]"},
            {"blade": "Astra SP {2}"},
            {"blade": "Astra SP (x4)"},
            # Dict blade entries (unmatched)
            {"blade": {"original": "Derby Extra (7)", "matched": None}},
            {"blade": {"original": "Derby Extra [1]", "matched": False}},
            {"blade": {"original": "Koraat (2)", "matched": None}},
            # Matched blade (should be ignored)
            {
                "blade": {
                    "original": "Gillette (3)",
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

    # Verify that use counts are stripped and entries are grouped correctly
    assert "Feather" in result_stdout
    assert "Astra SP" in result_stdout
    assert "Derby Extra" in result_stdout
    assert "Koraat" in result_stdout

    # Verify that use counts are NOT in the output
    assert "Feather (3)" not in result_stdout
    assert "Feather [5]" not in result_stdout
    assert "Astra SP {2}" not in result_stdout
    assert "Astra SP (x4)" not in result_stdout
    assert "Derby Extra (7)" not in result_stdout
    assert "Derby Extra [1]" not in result_stdout
    assert "Koraat (2)" not in result_stdout

    # Verify counts are correct (Feather appears twice, Derby Extra twice, others once)
    assert "(2 uses)" in result_stdout or "2 uses" in result_stdout  # Feather and Derby Extra
    assert "(1 uses)" in result_stdout or "1 uses" in result_stdout  # Astra SP and Koraat

    # Verify matched blade is not included
    assert "Gillette" not in result_stdout
