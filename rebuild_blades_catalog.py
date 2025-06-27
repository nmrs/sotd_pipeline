#!/usr/bin/env python3
"""
Rebuild blades.yaml from blades_brand_first.yaml by restructuring from brand-first to format-first.

Transforms from:
  brand:
    blade:
      format: X
      patterns: []

To:
  format:
    brand:
      blade:
        patterns: []
"""

from collections import defaultdict

import yaml


def rebuild_blades_catalog():
    """Rebuild the format-first blade catalog from the brand-first catalog."""

    # Load the old brand-first catalog
    with open("data/blades_brand_first.yaml", "r") as f:
        old_catalog = yaml.safe_load(f)

    # Create new format-first structure
    new_catalog = defaultdict(dict)

    # Process each brand
    for brand, blade_models in old_catalog.items():
        for blade_model, blade_data in blade_models.items():
            # Get format (default to DE if not specified)
            format_type = blade_data.get("format", "DE")

            # Initialize brand in format if not exists
            if brand not in new_catalog[format_type]:
                new_catalog[format_type][brand] = {}

            # Add blade model to brand
            new_catalog[format_type][brand][blade_model] = {
                "patterns": blade_data.get("patterns", [])
            }

    # Convert defaultdict to regular dict for YAML output
    new_catalog = dict(new_catalog)

    # Sort formats, brands, and models for consistent output
    sorted_catalog = {}
    for format_type in sorted(new_catalog.keys()):
        sorted_catalog[format_type] = {}
        for brand in sorted(new_catalog[format_type].keys(), key=str):
            sorted_catalog[format_type][brand] = {}
            for blade_model in sorted(new_catalog[format_type][brand].keys(), key=str):
                sorted_catalog[format_type][brand][blade_model] = new_catalog[format_type][brand][
                    blade_model
                ]

    # Write the new catalog
    with open("data/blades.yaml", "w") as f:
        yaml.dump(sorted_catalog, f, default_flow_style=False, indent=2, sort_keys=False)

    # Print summary
    print("Blade catalog rebuilt successfully!")
    print(f"Formats: {len(sorted_catalog)}")
    for format_type, brands in sorted_catalog.items():
        total_blades = sum(len(models) for models in brands.values())
        print(f"  {format_type}: {len(brands)} brands, {total_blades} blade models")

    return sorted_catalog


if __name__ == "__main__":
    rebuild_blades_catalog()
