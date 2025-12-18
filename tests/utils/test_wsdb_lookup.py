"""Tests for WSDB lookup utility with alias support."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from sotd.utils.wsdb_lookup import WSDBLookup


@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root with data directories."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Create data directories
    (project_root / "data" / "wsdb").mkdir(parents=True)
    (project_root / "data").mkdir(exist_ok=True)

    return project_root


@pytest.fixture
def mock_wsdb_data(temp_project_root):
    """Create mock WSDB data file."""
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"

    wsdb_data = [
        {
            "brand": "Barrister and Mann",
            "name": "Seville",
            "slug": "barrister-and-mann-seville",
            "type": "Soap",
        },
        {
            "brand": "The Artisan Shave Shoppe",
            "name": "Crisp Vetiver",
            "slug": "artisan-shave-shoppe-crisp-vetiver",
            "type": "Soap",
        },
        {
            "brand": "Stirling Soap Co.",
            "name": "Executive Man",
            "slug": "stirling-soap-co-executive-man",
            "type": "Soap",
        },
    ]

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    return wsdb_data


@pytest.fixture
def mock_pipeline_soaps(temp_project_root):
    """Create mock pipeline soaps.yaml with aliases."""
    soaps_file = temp_project_root / "data" / "soaps.yaml"

    soaps_data = {
        "Barrister and Mann": {
            "patterns": ["barrister.*mann"],
            "scents": {
                "Seville": {
                    "patterns": ["seville"],
                },
            },
        },
        "The Artisan Soap Shoppe": {
            "patterns": ["artisan.*soap.*shoppe"],
            "aliases": ["The Artisan Shave Shoppe"],
            "scents": {
                "Crisp Vetiver": {
                    "patterns": ["crisp.*vetiver"],
                },
            },
        },
        "Stirling Soap Co.": {
            "patterns": ["stirling"],
            "scents": {
                "Executive Man": {
                    "patterns": ["executive.*man"],
                    "alias": "Executive Man Scent",
                },
            },
        },
    }

    with soaps_file.open("w", encoding="utf-8") as f:
        yaml.dump(soaps_data, f)

    return soaps_data


def test_canonical_brand_scent_match(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test matching with canonical brand and scent."""
    lookup = WSDBLookup(project_root=temp_project_root)

    slug = lookup.get_wsdb_slug("Barrister and Mann", "Seville")

    assert slug == "barrister-and-mann-seville"


def test_brand_alias_match(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test matching with brand alias."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # "The Artisan Soap Shoppe" has alias "The Artisan Shave Shoppe"
    # WSDB has "The Artisan Shave Shoppe" - should match via alias
    slug = lookup.get_wsdb_slug("The Artisan Soap Shoppe", "Crisp Vetiver")

    assert slug == "artisan-shave-shoppe-crisp-vetiver"


def test_scent_alias_match(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test matching with scent alias."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # "Stirling Soap Co." has scent "Executive Man" with alias "Executive Man Scent"
    # Remove canonical entry and add only alias entry to test alias matching
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    # Remove canonical "Executive Man" entry
    wsdb_data = [item for item in wsdb_data if not (item.get("brand") == "Stirling Soap Co." and item.get("name") == "Executive Man")]

    # Add entry with alias name only
    wsdb_data.append(
        {
            "brand": "Stirling Soap Co.",
            "name": "Executive Man Scent",
            "slug": "stirling-executive-man-scent",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Now test - should match via scent alias (since canonical doesn't exist)
    lookup = WSDBLookup(project_root=temp_project_root)
    slug = lookup.get_wsdb_slug("Stirling Soap Co.", "Executive Man")

    # Should match the alias entry
    assert slug == "stirling-executive-man-scent"


def test_brand_alias_and_scent_alias_match(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test matching with both brand alias and scent alias."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Remove canonical entry first
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    # Remove canonical "Crisp Vetiver" entry
    wsdb_data = [item for item in wsdb_data if not (item.get("brand") == "The Artisan Shave Shoppe" and item.get("name") == "Crisp Vetiver")]

    # Add WSDB entry that matches both aliases
    wsdb_data.append(
        {
            "brand": "The Artisan Shave Shoppe",  # Brand alias
            "name": "Crisp Vetiver Alias",  # Scent alias (if we add it)
            "slug": "artisan-shave-shoppe-crisp-vetiver-alias",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Add scent alias to pipeline
    soaps_file = temp_project_root / "data" / "soaps.yaml"
    with soaps_file.open("r", encoding="utf-8") as f:
        soaps_data = yaml.safe_load(f)

    soaps_data["The Artisan Soap Shoppe"]["scents"]["Crisp Vetiver"]["alias"] = "Crisp Vetiver Alias"

    with soaps_file.open("w", encoding="utf-8") as f:
        yaml.dump(soaps_data, f)

    # Test - should match via both aliases (since canonical doesn't exist)
    lookup = WSDBLookup(project_root=temp_project_root)
    slug = lookup.get_wsdb_slug("The Artisan Soap Shoppe", "Crisp Vetiver")

    assert slug == "artisan-shave-shoppe-crisp-vetiver-alias"


def test_no_match(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test when no match is found."""
    lookup = WSDBLookup(project_root=temp_project_root)

    slug = lookup.get_wsdb_slug("Unknown Brand", "Unknown Scent")

    assert slug is None


def test_brand_without_aliases(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test matching with brand that has no aliases."""
    lookup = WSDBLookup(project_root=temp_project_root)

    slug = lookup.get_wsdb_slug("Barrister and Mann", "Seville")

    assert slug == "barrister-and-mann-seville"


def test_scent_without_alias(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test matching with scent that has no alias."""
    lookup = WSDBLookup(project_root=temp_project_root)

    slug = lookup.get_wsdb_slug("Barrister and Mann", "Seville")

    assert slug == "barrister-and-mann-seville"


def test_empty_brand_or_scent(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test with empty brand or scent."""
    lookup = WSDBLookup(project_root=temp_project_root)

    assert lookup.get_wsdb_slug("", "Seville") is None
    assert lookup.get_wsdb_slug("Barrister and Mann", "") is None
    assert lookup.get_wsdb_slug("", "") is None


def test_missing_wsdb_file(temp_project_root, mock_pipeline_soaps):
    """Test when WSDB file doesn't exist."""
    lookup = WSDBLookup(project_root=temp_project_root)

    slug = lookup.get_wsdb_slug("Barrister and Mann", "Seville")

    assert slug is None


def test_missing_soaps_yaml(temp_project_root, mock_wsdb_data):
    """Test when soaps.yaml doesn't exist (should still work for canonical matches)."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Should still match canonical brand/scent even without soaps.yaml
    slug = lookup.get_wsdb_slug("Barrister and Mann", "Seville")

    assert slug == "barrister-and-mann-seville"


def test_case_insensitive_matching(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test that matching is case-insensitive."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Test various case combinations
    assert lookup.get_wsdb_slug("barrister and mann", "seville") == "barrister-and-mann-seville"
    assert lookup.get_wsdb_slug("BARRISTER AND MANN", "SEVILLE") == "barrister-and-mann-seville"
    assert lookup.get_wsdb_slug("Barrister And Mann", "Seville") == "barrister-and-mann-seville"


def test_unicode_normalization(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test that Unicode normalization works correctly."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry with Unicode characters
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Café",
            "name": "Espresso",
            "slug": "cafe-espresso",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Should match regardless of Unicode normalization
    slug = lookup.get_wsdb_slug("Café", "Espresso")
    assert slug == "cafe-espresso"


def test_virtual_alias_brand_stripped_soap(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual alias: brand with trailing 'Soap' should match WSDB without 'Soap'."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry without "Soap" in brand name
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Talbot Shaving",
            "name": "Gates of the Arctic",
            "slug": "talbot-shaving-gates-of-the-arctic",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Query with "Soap" appended - should match via virtual alias
    slug = lookup.get_wsdb_slug("Talbot Shaving Soap", "Gates of the Arctic")
    assert slug == "talbot-shaving-gates-of-the-arctic"


def test_virtual_alias_scent_stripped_soap(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual alias: scent with trailing 'Soap' should match WSDB without 'Soap'."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry without "Soap" in scent name
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Barrister and Mann",
            "name": "Gates of the Arctic",
            "slug": "barrister-and-mann-gates-of-the-arctic",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Query with "Soap" appended to scent - should match via virtual alias
    slug = lookup.get_wsdb_slug("Barrister and Mann", "Gates of the Arctic Soap")
    assert slug == "barrister-and-mann-gates-of-the-arctic"


def test_virtual_alias_both_stripped_soap(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual alias: both brand and scent with trailing 'Soap' should match."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry without "Soap" in either name
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Talbot Shaving",
            "name": "Gates of the Arctic",
            "slug": "talbot-shaving-gates-of-the-arctic",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Query with "Soap" appended to both - should match via virtual alias
    slug = lookup.get_wsdb_slug("Talbot Shaving Soap", "Gates of the Arctic Soap")
    assert slug == "talbot-shaving-gates-of-the-arctic"


def test_virtual_alias_case_insensitive(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual alias: case-insensitive matching for 'soap'."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Test Brand",
            "name": "Test Scent",
            "slug": "test-brand-test-scent",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Test various case combinations
    assert lookup.get_wsdb_slug("Test Brand Soap", "Test Scent") == "test-brand-test-scent"
    assert lookup.get_wsdb_slug("Test Brand SOAP", "Test Scent") == "test-brand-test-scent"
    assert lookup.get_wsdb_slug("Test Brand", "Test Scent Soap") == "test-brand-test-scent"
    assert lookup.get_wsdb_slug("Test Brand", "Test Scent SOAP") == "test-brand-test-scent"


def test_virtual_alias_wsdb_side_stripped_soap(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual alias: WSDB entry with 'Soap' should match pipeline without 'Soap'."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry WITH "Soap" in brand name
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Test Brand Soap",
            "name": "Test Scent",
            "slug": "test-brand-soap-test-scent",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Query without "Soap" - should match via virtual alias on WSDB side
    slug = lookup.get_wsdb_slug("Test Brand", "Test Scent")
    assert slug == "test-brand-soap-test-scent"


def test_virtual_alias_no_stripping_when_not_at_end(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test that 'soap' is only stripped when at the end, not in the middle."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Soap Company",
            "name": "Test Scent",
            "slug": "soap-company-test-scent",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # "Soap" is in the middle, not at the end - should not be stripped
    # This should NOT match "Soap Company" (without "Soap" at end)
    slug = lookup.get_wsdb_slug("Soap Company", "Test Scent")
    assert slug == "soap-company-test-scent"

    # But "Soap Company Soap" should match "Soap Company" (stripping trailing "Soap")
    slug = lookup.get_wsdb_slug("Soap Company Soap", "Test Scent")
    assert slug == "soap-company-test-scent"


def test_virtual_pattern_accent_normalization(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual pattern: accented characters should match non-accented."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry with non-accented characters
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Cafe",
            "name": "Espresso",
            "slug": "cafe-espresso",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Query with accented characters - should match via accent normalization
    slug = lookup.get_wsdb_slug("Café", "Espresso")
    assert slug == "cafe-espresso"

    # Also test reverse: WSDB has accented, pipeline has non-accented
    wsdb_data.append(
        {
            "brand": "Café",
            "name": "Résumé",
            "slug": "cafe-resume",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    slug = lookup.get_wsdb_slug("Cafe", "Resume")
    assert slug == "cafe-resume"


def test_virtual_pattern_and_ampersand_normalization(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual pattern: 'and' and '&' should be treated as the same."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry with "and"
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Barrister and Mann",
            "name": "Seville",
            "slug": "barrister-and-mann-seville",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Query with "&" - should match via and/& normalization
    slug = lookup.get_wsdb_slug("Barrister & Mann", "Seville")
    assert slug == "barrister-and-mann-seville"

    # Also test reverse: WSDB has "&", pipeline has "and"
    wsdb_data.append(
        {
            "brand": "Test & Company",
            "name": "Scent",
            "slug": "test-and-company-scent",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    slug = lookup.get_wsdb_slug("Test and Company", "Scent")
    assert slug == "test-and-company-scent"


def test_virtual_pattern_combined_variations(temp_project_root, mock_wsdb_data, mock_pipeline_soaps):
    """Test virtual patterns: combinations of all variations."""
    lookup = WSDBLookup(project_root=temp_project_root)

    # Add WSDB entry
    wsdb_file = temp_project_root / "data" / "wsdb" / "software.json"
    with wsdb_file.open("r", encoding="utf-8") as f:
        wsdb_data = json.load(f)

    wsdb_data.append(
        {
            "brand": "Cafe",
            "name": "Espresso",
            "slug": "cafe-espresso",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    # Query with all variations: accented, trailing "Soap"
    slug = lookup.get_wsdb_slug("Café Soap", "Espresso Soap")
    assert slug == "cafe-espresso"

    # Test with "and" vs "&" and trailing "Soap"
    wsdb_data.append(
        {
            "brand": "Barrister and Mann",
            "name": "Seville",
            "slug": "barrister-and-mann-seville",
            "type": "Soap",
        }
    )

    with wsdb_file.open("w", encoding="utf-8") as f:
        json.dump(wsdb_data, f)

    slug = lookup.get_wsdb_slug("Barrister & Mann Soap", "Seville")
    assert slug == "barrister-and-mann-seville"

