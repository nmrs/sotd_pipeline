import json
from pathlib import Path


def save_month_file(month: str, result: dict, out_dir: Path = Path("data/extracted")) -> None:
    """
    Save the extraction result to a JSON file with the structure:
    {
        "meta": { ... },
        "data": [ ... ]
    }

    Parameters:
    - month: Month identifier in "YYYY-MM" format
    - result: Data to write to the file
    - out_dir: Directory where the file will be saved
    """
    out_path = out_dir / f"{month}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[DEBUG] Saving extraction result to: {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
