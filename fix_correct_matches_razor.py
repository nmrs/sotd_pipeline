import sys
from collections import defaultdict
from pathlib import Path

from sotd.utils.file_io import load_yaml_data, save_yaml_data
from sotd.utils.match_filter_utils import normalize_for_matching

CORRECT_MATCHES_PATH = Path("data/correct_matches.yaml")
BACKUP_PATH = Path("data/correct_matches.yaml.backup")


def main():
    data = load_yaml_data(CORRECT_MATCHES_PATH)
    if "razor" not in data:
        print("No razor section found in correct_matches.yaml")
        sys.exit(1)

    razor = data["razor"]
    changed = defaultdict(list)  # (brand, model) -> list of (original, normalized)
    removed = defaultdict(list)  # (brand, model) -> list of removed dupes
    new_razor = {}

    for brand, models in razor.items():
        new_razor[brand] = {}
        for model, originals in models.items():
            seen = {}
            new_list = []
            for orig in originals:
                norm = normalize_for_matching(orig, None, field="razor")
                if norm not in seen:
                    seen[norm] = orig
                    new_list.append(orig)
                    if orig != norm:
                        changed[(brand, model)].append((orig, norm))
                else:
                    removed[(brand, model)].append(orig)
            new_razor[brand][model] = new_list

    # Write backup
    CORRECT_MATCHES_PATH.replace(BACKUP_PATH)
    # Write new YAML
    data["razor"] = new_razor
    save_yaml_data(data, CORRECT_MATCHES_PATH)

    # Report
    print("=== Razor correct_matches.yaml cleanup summary ===")
    print("Changed (normalized):")
    for (brand, model), pairs in changed.items():
        if pairs:
            print(f"  {brand} / {model}:")
            for orig, norm in pairs:
                print(f"    - '{orig}' -> '{norm}'")
    print("\nRemoved duplicates:")
    for (brand, model), dupes in removed.items():
        if dupes:
            print(f"  {brand} / {model}:")
            for orig in dupes:
                print(f"    - '{orig}'")
    print("\nDone.")


if __name__ == "__main__":
    main()
