import yaml
from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches


def test_blade_format_aware_duplicate_integration(tmp_path):
    """
    Integration test: Only forbidden blade duplicates (same format) are flagged as errors,
    while legitimate format-aware duplicates are allowed.
    """
    # Setup correct_matches.yaml with both legitimate and forbidden duplicates
    correct_matches_data = {
        "blade": {
            "GEM": {
                "Personna": {
                    "GEM PTFE": ["Accuforge"],  # GEM format
                }
            },
            "DE": {
                "Personna": {
                    "Lab Blue": ["Accuforge"],  # DE format (legitimate duplicate)
                    "Med Prep": ["Accuforge"],  # DE format (forbidden duplicate)
                }
            },
        }
    }
    # Setup blades.yaml with format information
    catalog_data = {
        "GEM": {"Personna": {"GEM PTFE": {"patterns": ["accuforge"], "format": "GEM"}}},
        "DE": {
            "Personna": {
                "Lab Blue": {"patterns": ["accuforge"], "format": "DE"},
                "Med Prep": {"patterns": ["accuforge"], "format": "DE"},
            }
        },
    }
    # Write temp files
    correct_matches_file = tmp_path / "correct_matches.yaml"
    blades_file = tmp_path / "blades.yaml"
    with correct_matches_file.open("w") as f:
        yaml.dump(correct_matches_data, f)
    with blades_file.open("w") as f:
        yaml.dump(catalog_data, f)
    # Run validator
    validator = ValidateCorrectMatches()
    validator._data_dir = tmp_path  # type: ignore
    validator.correct_matches = validator._load_correct_matches()

    # Load catalog data properly using the new method
    validator.catalog_cache["blade"] = validator._load_catalog("blade")

    print("DEBUG: correct_matches:", validator.correct_matches)
    print("DEBUG: catalog_cache['blade']:", validator.catalog_cache["blade"])
    issues = validator._check_duplicate_strings("blade")
    print("DEBUG: issues:", issues)
    # There should be exactly one issue, for the forbidden duplicate (Lab Blue & Med Prep, both DE)
    assert len(issues) == 1, f"Expected 1 issue, got: {issues}"
    issue = issues[0]
    assert issue["issue_type"] == "duplicate_string"
    assert issue["duplicate_string"] == "Accuforge"
    # The legitimate duplicate (GEM PTFE vs Lab Blue) should NOT be flagged
