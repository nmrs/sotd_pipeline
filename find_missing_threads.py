import json
from pathlib import Path

COMMENTS_DIR = Path("data/comments")


def main():
    missing = {}
    for fname in sorted(COMMENTS_DIR.glob("*.json")):
        try:
            with open(fname, "r", encoding="utf-8") as f:
                obj = json.load(f)
            meta = obj.get("meta", {})
            month = meta.get("month")
            missing_days = meta.get("missing_days", [])
            if missing_days:
                missing[month or fname.name] = missing_days
        except Exception as e:
            print(f"[WARN] Could not process {fname}: {e}")
    if not missing:
        print("No missing days found in any month.")
    else:
        print("Missing threads by month:")
        for month, days in missing.items():
            print(f"{month}: {', '.join(days)}")


if __name__ == "__main__":
    main()
