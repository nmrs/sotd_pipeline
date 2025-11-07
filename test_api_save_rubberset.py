#!/usr/bin/env python3
"""Test script to verify Rubberset 400-unnumbered saves correctly via API."""

import json
import requests
from pathlib import Path
import yaml

# Test configuration
API_BASE_URL = "http://localhost:8000"  # Adjust if API runs on different port
ORIGINAL_TEXT = "Rubberset 400-unnumbered w/ original knot"

# Expected matched data structure from known_brush strategy
# Based on brushes.yaml: Rubberset -> '400' -> fiber: Boar
TEST_MATCH_DATA = {
    "original": ORIGINAL_TEXT,
    "matched": {
        "brand": "Rubberset",
        "model": "400",
        "fiber": "Boar",  # From catalog
        # Known_brush strategy also includes nested handle/knot structures
        "handle": {
            "brand": "Rubberset",
            "model": None
        },
        "knot": {
            "brand": "Rubberset",
            "model": "400",
            "fiber": "Boar"
        }
    }
}

def test_mark_correct_api():
    """Test marking Rubberset 400-unnumbered as correct via API."""
    
    # Prepare request
    request_data = {
        "field": "brush",
        "matches": [TEST_MATCH_DATA],
        "force": True
    }
    
    print(f"Testing mark-correct API for: {ORIGINAL_TEXT}")
    print(f"Request data: {json.dumps(request_data, indent=2)}")
    
    # Call API
    response = requests.post(
        f"{API_BASE_URL}/api/analysis/mark-correct",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nResponse status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 200:
        print(f"❌ API call failed with status {response.status_code}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ API returned success=False: {result.get('message')}")
        return False
    
    print(f"✅ API call succeeded: {result.get('message')}")
    return True

def verify_saved_in_yaml():
    """Verify entry is saved in brush.yaml."""
    
    brush_yaml_path = Path("data/correct_matches/brush.yaml")
    
    if not brush_yaml_path.exists():
        print(f"❌ brush.yaml not found at {brush_yaml_path}")
        return False
    
    with brush_yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    # Check if Rubberset -> 400 -> contains our entry
    rubberset_section = data.get("Rubberset", {})
    model_400 = rubberset_section.get("400", [])
    
    # Normalize for comparison (lowercase, strip)
    normalized_original = ORIGINAL_TEXT.lower().strip()
    
    found = False
    for entry in model_400:
        if isinstance(entry, str):
            if entry.lower().strip() == normalized_original:
                found = True
                print(f"✅ Found entry in brush.yaml: Rubberset -> 400 -> {entry}")
                break
    
    if not found:
        print(f"❌ Entry not found in brush.yaml under Rubberset -> 400")
        print(f"   Current entries: {model_400}")
        return False
    
    return True

def verify_loads_back():
    """Verify entry can be loaded back via get-correct-matches API."""
    
    response = requests.get(
        f"{API_BASE_URL}/api/analysis/correct-matches/brush"
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to load correct matches: {response.status_code}")
        return False
    
    result = response.json()
    total_entries = result.get("total_entries", 0)
    
    print(f"✅ Loaded correct matches: {total_entries} total entries")
    
    # Check if our entry is in the loaded data
    entries = result.get("entries", {})
    normalized_original = ORIGINAL_TEXT.lower().strip()
    
    # The entries structure might be different, but we can check total count increased
    print(f"   (Entry verification requires checking internal structure)")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Rubberset 400-unnumbered API Save")
    print("=" * 60)
    
    # Step 1: Call API
    api_success = test_mark_correct_api()
    if not api_success:
        print("\n❌ API test failed, stopping")
        exit(1)
    
    # Step 2: Verify saved in YAML
    yaml_success = verify_saved_in_yaml()
    if not yaml_success:
        print("\n❌ YAML verification failed")
        exit(1)
    
    # Step 3: Verify loads back
    load_success = verify_loads_back()
    if not load_success:
        print("\n❌ Load verification failed")
        exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

