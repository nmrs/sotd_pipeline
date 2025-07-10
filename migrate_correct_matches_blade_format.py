import yaml
from pathlib import Path

# Paths
input_path = Path("data/correct_matches.yaml")
output_path = Path("data/correct_matches.yaml.migrated")
catalog_path = Path("data/blades.yaml")

# Load current correct_matches.yaml
with input_path.open("r", encoding="utf-8") as f:
    correct_matches = yaml.safe_load(f)

# Load blade catalog for format mapping
with catalog_path.open("r", encoding="utf-8") as f:
    catalog = yaml.safe_load(f)

# Only migrate the blade section
blade_matches = correct_matches.get("blade", {})

# Build new format-first structure for blades
format_first_blades = {}

# For each brand/model in the old structure, find its format in the catalog
for brand, models in blade_matches.items():
    if not isinstance(models, dict):
        continue
    for model, entries in models.items():
        # Find the format for this brand/model in the catalog
        found = False
        for fmt, brands in catalog.items():
            if brand in brands and model in brands[brand]:
                format_first_blades.setdefault(fmt, {})
                format_first_blades[fmt].setdefault(brand, {})
                format_first_blades[fmt][brand][model] = list(entries)
                found = True
                break
        if not found:
            # If not found, default to DE
            format_first_blades.setdefault("DE", {})
            format_first_blades["DE"].setdefault(brand, {})
            format_first_blades["DE"][brand][model] = list(entries)

# Compose new correct_matches structure
new_correct_matches = dict(correct_matches)  # Copy all other sections
new_correct_matches["blade"] = format_first_blades

# Write to output file for review
with output_path.open("w", encoding="utf-8") as f:
    yaml.dump(new_correct_matches, f, sort_keys=False, allow_unicode=True)

print(f"Migration complete. Review the migrated file at {output_path}")
