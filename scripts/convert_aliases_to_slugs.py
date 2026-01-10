#!/usr/bin/env python3
"""Convert existing aliases in soaps.yaml to wsdb_slug fields.

This script:
1. Loads soaps.yaml
2. For each scent with an alias, uses current WSDB lookup to find the slug
3. Replaces alias: with wsdb_slug:
4. Removes brand-level aliases: lists
5. Saves updated YAML
"""

import json
import sys
from pathlib import Path

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sotd.utils.wsdb_lookup import WSDBLookup


def convert_aliases_to_slugs():
    """Convert all aliases to slugs in soaps.yaml."""
    soaps_file = project_root / "data" / "soaps.yaml"
    
    if not soaps_file.exists():
        print(f"Error: {soaps_file} not found")
        return False
    
    # Load soaps.yaml
    print(f"Loading {soaps_file}...")
    with soaps_file.open("r", encoding="utf-8") as f:
        soaps_data = yaml.safe_load(f) or {}
    
    # Initialize WSDB lookup (uses current alias logic for conversion)
    lookup = WSDBLookup(project_root=project_root)
    
    converted_count = 0
    removed_brand_aliases = 0
    failed_conversions = []
    
    # Process each brand
    for brand, brand_data in soaps_data.items():
        if not isinstance(brand_data, dict):
            continue
        
        # Remove brand-level aliases
        if "aliases" in brand_data:
            removed_brand_aliases += 1
            del brand_data["aliases"]
        
        # Process scents with aliases
        if "scents" in brand_data:
            for scent_name, scent_data in brand_data["scents"].items():
                if not isinstance(scent_data, dict):
                    continue
                
                if "alias" in scent_data:
                    alias = scent_data["alias"]
                    print(f"Converting: {brand} - {scent_name} (alias: {alias})")
                    
                    # Use current lookup logic to find slug
                    slug = lookup.get_wsdb_slug(brand, scent_name)
                    
                    if slug:
                        # Replace alias with wsdb_slug
                        scent_data["wsdb_slug"] = slug
                        del scent_data["alias"]
                        converted_count += 1
                        print(f"  ✓ Converted to slug: {slug}")
                    else:
                        # Try with alias as scent name
                        slug = lookup.get_wsdb_slug(brand, alias)
                        if slug:
                            scent_data["wsdb_slug"] = slug
                            del scent_data["alias"]
                            converted_count += 1
                            print(f"  ✓ Converted to slug (using alias as scent): {slug}")
                        else:
                            failed_conversions.append(f"{brand} - {scent_name} (alias: {alias})")
                            print(f"  ✗ Failed to find slug for alias: {alias}")
    
    # Save updated YAML
    print(f"\nSaving updated {soaps_file}...")
    temp_file = soaps_file.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as f:
        yaml.dump(soaps_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    temp_file.replace(soaps_file)
    
    print(f"\nConversion complete:")
    print(f"  - Converted {converted_count} scent aliases to slugs")
    print(f"  - Removed {removed_brand_aliases} brand alias lists")
    if failed_conversions:
        print(f"  - Failed to convert {len(failed_conversions)} aliases:")
        for failed in failed_conversions:
            print(f"    - {failed}")
        return False
    
    return True


if __name__ == "__main__":
    success = convert_aliases_to_slugs()
    sys.exit(0 if success else 1)
