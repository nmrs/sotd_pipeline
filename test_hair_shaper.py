#!/usr/bin/env python3
"""
Test script for context-aware blade matching with Hair Shaper case.
"""

from sotd.match.match import match_record


def test_hair_shaper_case():
    """Test the specific case: Weck Hair Shaper + Personna blade"""
    print("Testing Hair Shaper case...")

    record = {"razor": "Weck Hair Shaper", "blade": "Personna (5)"}

    result = match_record(record)

    print(f"Input: {record}")
    print(f"Razor matched: {result['razor'].get('matched', {})}")
    print(f"Blade matched: {result['blade'].get('matched', {})}")
    print(f"Blade match_type: {result['blade'].get('match_type', {})}")

    # Verify razor is correctly matched
    razor_matched = result["razor"].get("matched", {})
    blade_matched = result["blade"].get("matched", {})

    print("\nAnalysis:")
    print(f"Razor format: {razor_matched.get('format', 'NOT_FOUND')}")
    print(f"Blade format: {blade_matched.get('format', 'NOT_FOUND')}")

    # Check if context-aware matching worked
    if (
        razor_matched.get("format") == "Shavette (Hair Shaper)"
        and blade_matched.get("format") == "Hair Shaper"
    ):
        print("✅ SUCCESS: Context-aware blade matching worked correctly!")
        print("   Personna blade correctly matched to Hair Shaper format")
    else:
        print("❌ FAILURE: Context-aware blade matching did not work as expected")
        print("   Expected: Razor=Shavette (Hair Shaper), Blade=Hair Shaper")
        print(f"   Got: Razor={razor_matched.get('format')}, Blade={blade_matched.get('format')}")


def test_normal_de_case():
    """Test normal DE case to ensure it still works"""
    print("\nTesting normal DE case...")

    record = {"razor": "Merkur 37C", "blade": "Personna (5)"}

    result = match_record(record)

    print(f"Input: {record}")
    print(f"Razor matched: {result['razor'].get('matched', {})}")
    print(f"Blade matched: {result['blade'].get('matched', {})}")

    razor_matched = result["razor"].get("matched", {})
    blade_matched = result["blade"].get("matched", {})

    print(f"Razor format: {razor_matched.get('format', 'NOT_FOUND')}")
    print(f"Blade format: {blade_matched.get('format', 'NOT_FOUND')}")

    if razor_matched.get("format") == "DE" and blade_matched.get("format") == "DE":
        print("✅ SUCCESS: Normal DE case still works!")
    else:
        print("❌ FAILURE: Normal DE case broken")


if __name__ == "__main__":
    test_hair_shaper_case()
    test_normal_de_case()
