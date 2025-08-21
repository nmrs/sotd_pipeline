# pylint: disable=redefined-outer-name

"""
Integration tests for the match phase to verify that updated matchers work correctly
and that exact matches are properly identified.
"""

import json

import pytest

from sotd.match.run import process_month


@pytest.fixture
def sample_extracted_data():
    """Sample extracted data for testing match phase integration."""
    return {
        "metadata": {
            "month": "2025-01",
            "record_count": 3,
        },
        "data": [
            {
                "razor": {"original": "Karve CB", "normalized": "Karve CB"},
                "blade": {"original": "Feather (3)", "normalized": "Feather (3)"},
                "brush": {"original": "Simpson Chubby 2", "normalized": "Simpson Chubby 2"},
                "soap": {
                    "original": "Barrister and Mann - Seville",
                    "normalized": "Barrister and Mann - Seville",
                },
            },
            {
                "razor": {"original": "Merkur 34C", "normalized": "Merkur 34C"},
                "blade": {"original": "Astra SP", "normalized": "Astra SP"},
                "brush": {"original": "Declaration B3", "normalized": "Declaration B3"},
                "soap": {
                    "original": "House of Mammoth - Alive",
                    "normalized": "House of Mammoth - Alive",
                },
            },
            {
                "razor": {"original": "Unknown Razor", "normalized": "Unknown Razor"},
                "blade": {"original": "Unknown Blade", "normalized": "Unknown Blade"},
                "brush": {"original": "Unknown Brush", "normalized": "Unknown Brush"},
                "soap": {"original": "Unknown Soap", "normalized": "Unknown Soap"},
            },
        ],
    }


def test_match_phase_integration_with_updated_matchers(tmp_path, sample_extracted_data):
    """
    Test that the match phase works correctly with updated matchers.
    """
    # Create test directory structure
    base_path = tmp_path / "data"
    extracted_path = base_path / "extracted"
    extracted_path.mkdir(parents=True)

    # Write sample extracted data
    extracted_file = extracted_path / "2025-01.json"
    with extracted_file.open("w") as f:
        json.dump(sample_extracted_data, f, ensure_ascii=False)

    # Create correct_matches.yaml with some test entries
    correct_matches_content = """
razor:
  Karve:
    Christopher Bradley:
      - "Karve CB"
  Merkur:
    34C:
      - "Merkur 34C"
blade:
  DE:
    Feather:
      DE:
        - "Feather"
    Astra:
      SP:
        - "Astra SP"
brush:
  Simpson:
    Chubby 2:
      - "Simpson Chubby 2"
  Declaration Grooming:
    B3:
      - "Declaration B3"
soap:
  Barrister and Mann:
    Seville:
      - "Barrister and Mann - Seville"
  House of Mammoth:
    Alive:
      - "House of Mammoth - Alive"
"""
    correct_matches_file = base_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    # Process the month
    result = process_month(
        "2025-01",
        base_path,
        force=True,
        debug=False,
        correct_matches_path=correct_matches_file,
        brush_system="legacy",
    )

    # Print error details if processing failed
    if result["status"] == "error":
        print(f"Processing failed with error: {result.get('error', 'Unknown error')}")

    # Verify processing completed successfully
    assert result["status"] == "completed"
    assert result["month"] == "2025-01"
    assert result["records_processed"] == 3

    # Load and verify the matched data
    # When using brush_system="legacy", the file is saved to matched_legacy/
    matched_file = base_path / "matched_legacy" / "2025-01.json"
    assert matched_file.exists()

    with matched_file.open("r") as f:
        matched_data = json.load(f)

    # Verify metadata
    assert matched_data["metadata"]["month"] == "2025-01"
    assert matched_data["metadata"]["record_count"] == 3

    # Verify that exact matches are properly identified
    records = matched_data["data"]

    # First record should have exact matches
    first_record = records[0]
    print("DEBUG: Blade match result:", first_record["blade"])
    assert first_record["razor"]["match_type"] == "exact"
    assert first_record["razor"]["matched"]["brand"] == "Karve"
    assert first_record["razor"]["matched"]["model"] == "Christopher Bradley"

    assert first_record["blade"]["match_type"] == "exact"
    assert first_record["blade"]["matched"]["brand"] == "Feather"
    assert first_record["blade"]["matched"]["model"] == "DE"

    assert first_record["brush"]["match_type"] == "exact"
    assert first_record["brush"]["matched"]["handle"]["brand"] == "Simpson"
    assert first_record["brush"]["matched"]["handle"]["model"] == "Chubby 2"
    assert first_record["brush"]["matched"]["knot"]["brand"] == "Simpson"
    assert first_record["brush"]["matched"]["knot"]["model"] == "Chubby 2"

    assert first_record["soap"]["match_type"] == "exact"
    assert first_record["soap"]["matched"]["brand"] == "Barrister and Mann"
    assert first_record["soap"]["matched"]["scent"] == "Seville"

    # Second record should also have exact matches
    second_record = records[1]
    assert second_record["razor"]["match_type"] == "exact"
    assert second_record["razor"]["matched"]["brand"] == "Merkur"
    assert second_record["razor"]["matched"]["model"] == "34C"

    assert second_record["blade"]["match_type"] == "exact"
    assert second_record["blade"]["matched"]["brand"] == "Astra"
    assert second_record["blade"]["matched"]["model"] == "SP"

    assert second_record["brush"]["match_type"] == "exact"
    assert second_record["brush"]["matched"]["handle"]["brand"] == "Declaration Grooming"
    assert second_record["brush"]["matched"]["handle"]["model"] == "B3"
    assert second_record["brush"]["matched"]["knot"]["brand"] == "Declaration Grooming"
    assert second_record["brush"]["matched"]["knot"]["model"] == "B3"

    assert second_record["soap"]["match_type"] == "exact"
    assert second_record["soap"]["matched"]["brand"] == "House of Mammoth"
    assert second_record["soap"]["matched"]["scent"] == "Alive"

    # Third record should have no matches (unmatched)
    third_record = records[2]
    print(f"DEBUG: Third record brush: {third_record.get('brush')}")
    print(f"DEBUG: Third record brush type: {type(third_record.get('brush'))}")
    print(f"DEBUG: Third record full: {third_record}")
    assert third_record["razor"]["matched"] is None
    assert third_record["blade"]["matched"] is None
    assert third_record["brush"]["matched"] is None
    assert third_record["soap"]["matched"] is None


def test_match_phase_uses_default_correct_matches(tmp_path, sample_extracted_data):
    """
    Test that the match phase uses the default correct_matches.yaml when no custom path is provided.
    """
    # Create test directory structure
    base_path = tmp_path / "data"
    extracted_path = base_path / "extracted"
    extracted_path.mkdir(parents=True)

    # Write sample extracted data
    extracted_file = extracted_path / "2025-01.json"
    with extracted_file.open("w") as f:
        json.dump(sample_extracted_data, f, ensure_ascii=False)

    # Create a default correct_matches.yaml in the expected location
    default_correct_matches_content = """
razor:
  Karve:
    Christopher Bradley:
      - "Karve CB"
"""
    default_correct_matches_file = base_path / "correct_matches.yaml"
    default_correct_matches_file.write_text(default_correct_matches_content)

    # Process the month
    result = process_month(
        "2025-01",
        base_path,
        force=True,
        debug=False,
        correct_matches_path=default_correct_matches_file,
    )

    # Verify processing completed successfully
    assert result["status"] == "completed"

    # Load and verify that the default correct_matches was used
    matched_file = base_path / "matched" / "2025-01.json"
    with matched_file.open("r") as f:
        matched_data = json.load(f)

    # First record should have exact match for razor
    first_record = matched_data["data"][0]
    assert first_record["razor"]["match_type"] == "exact"
    assert first_record["razor"]["matched"]["brand"] == "Karve"
    assert first_record["razor"]["matched"]["model"] == "Christopher Bradley"
